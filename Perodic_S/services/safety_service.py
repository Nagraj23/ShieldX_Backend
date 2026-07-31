import json
import logging
from typing import Dict, Any, List
from passlib.context import CryptContext
from config.redis_config import get_redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger("safety_service")

class SafetyService:
    def __init__(self):
        self.redis_client = get_redis_client()

    async def start_safety_session(
        self, 
        child_id: str, 
        mode: str, 
        estimated_duration_minutes: int = 0, 
        safe_code_hash: str = "", 
        duress_code_hash: str = "", 
        parent_contacts: List[str] = []
    ) -> bool:
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        
        interval_minutes = 1  
        ttl_seconds = interval_minutes * 60

        session_data = {
            "child_id": child_id,
            "mode": mode,
            "safe_code_hash": safe_code_hash,
            "duress_code_hash": duress_code_hash,
            "parent_contacts": parent_contacts,
            "interval_minutes": interval_minutes,
            "status": "ACTIVE"
        }
        
        await self.redis_client.set(session_key, json.dumps(session_data))
        await self.redis_client.setex(timer_key, ttl_seconds, "TICKING")
        
        logger.info(f"Safety tracking ({mode}) spawned for child {child_id}. Interval set to {interval_minutes}m (TEST MODE).")
        return True

    async def verify_user_code(self, child_id: str, plain_code: str) -> Dict[str, Any]:
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        response_timer_key = f"periodic:response:{child_id}"
        
        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return {"status": "ERROR", "message": "No active safety tracking found for this user context."}
            
        session_data = json.loads(raw_session)
        
        if pwd_context.verify(plain_code, session_data["safe_code_hash"]):
            await self.redis_client.delete(response_timer_key)
            await self.redis_client.delete(f"periodic:retry:{child_id}")
            
            ttl_seconds = int(session_data["interval_minutes"]) * 60
            
            session_data["status"] = "ACTIVE"
            await self.redis_client.set(session_key, json.dumps(session_data))
            await self.redis_client.setex(timer_key, ttl_seconds, "TICKING")
            
            logger.info(f"Child {child_id} verified SAFE. Timer loop reset.")
            return {"status": "SUCCESS", "message": "All clear received. Next countdown loop initialized."}
            
        elif pwd_context.verify(plain_code, session_data["duress_code_hash"]):
            logger.warning(f"CRITICAL: Child {child_id} entered silent DURESS PIN!")
            
            await self.trigger_emergency_alert(
                child_id=child_id, 
                target_contacts=session_data["parent_contacts"], 
                reason="DURESS_TRIGGERED"
            )
            
            await self.redis_client.delete(timer_key, response_timer_key, session_key, f"periodic:retry:{child_id}")
            
            return {"status": "SUCCESS", "message": "All clear received. Next countdown loop initialized."}
            
        else:
            return {"status": "INVALID_CODE", "message": "Incorrect combination entered. Please verify and try again."}

    async def trigger_emergency_alert(self, child_id: str, target_contacts: List[str], reason: str):
        alert_payload = {
            "event": "SAFETY_ALERT_SOS",
            "child_id": child_id,
            "reason": reason,
            "recipients": target_contacts,
            "message": "ShieldX Security Alert: Your child failed their check-in prompt or entered a duress code."
        }
        channel_pipe = "notification_channel_stream"
        await self.redis_client.publish(channel_pipe, json.dumps(alert_payload))
        logger.info(f"Emergency payload dispatched for child {child_id}")

    async def get_session_status(self, child_id: str) -> Dict[str, Any]:
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        response_timer_key = f"periodic:response:{child_id}"

        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return {"status": "NOT_FOUND", "message": "No active safety session found."}

        session_data = json.loads(raw_session)
        
        remaining_seconds = await self.redis_client.ttl(timer_key)
        if remaining_seconds < 0:
            remaining_seconds = await self.redis_client.ttl(response_timer_key)

        return {
            "status": session_data.get("status", "ACTIVE"),
            "child_id": child_id,
            "interval_minutes": session_data.get("interval_minutes"),
            "remaining_seconds": max(remaining_seconds, 0)
        }

    async def stop_safety_session(self, child_id: str) -> Dict[str, Any]:
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        response_timer_key = f"periodic:response:{child_id}"

        if not await self.redis_client.exists(session_key):
            return {"status": "NOT_FOUND", "message": "No active safety session found."}

        await self.redis_client.delete(session_key, timer_key, response_timer_key, f"periodic:retry:{child_id}")
        logger.info(f"Periodic safety session stopped for child {child_id}")

        return {"status": "SUCCESS", "message": "Periodic safety session stopped successfully."}

    async def send_checkin_request(self, child_id: str) -> None:
        session_key = f"periodic:session:{child_id}"
        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return

        session_data = json.loads(raw_session)
        session_data["status"] = "CHALLENGED"
        await self.redis_client.set(session_key, json.dumps(session_data))

        response_timer_key = f"periodic:response:{child_id}"
        await self.redis_client.setex(response_timer_key, 30, "WAITING_FOR_RESPONSE")

        # Event payload published to Redis channel for UI and notification services to catch
        checkin_payload = {
            "event": "PERIODIC_CHECKIN",
            "type": "SAFETY_CHALLENGE",
            "child_id": child_id,
            "recipients": [child_id],
            "title": "🛡️ ShieldX Safety Check",
            "message": "Are you safe? Tap here to enter your safety code within 30 seconds."
        }

        await self.redis_client.publish("notification_channel_stream", json.dumps(checkin_payload))
        logger.info(f"Periodic check-in published and status set to CHALLENGED for child {child_id}")

    async def handle_no_response(self, child_id: str):
        session_key = f"periodic:session:{child_id}"
        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return

        session_data = json.loads(raw_session)
        
        await self.trigger_emergency_alert(
            child_id=child_id,
            target_contacts=session_data["parent_contacts"],
            reason="NO_RESPONSE"
        )

        await self.redis_client.delete(session_key, f"periodic:response:{child_id}", f"periodic:retry:{child_id}")
        logger.info(f"Emergency SOS finalized and cleaned up for child {child_id}")