import json
import logging
import random
from typing import Dict, Any, List
from passlib.context import CryptContext
from config.redis_config import get_redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger("safety_service")

class SafetyService:
    def __init__(self):
        self.redis_client = get_redis_client()
        self.MAX_RETRIES = 3

    async def calculate_next_interval(self, mode: str, estimated_duration_minutes: int) -> int:
        mode_upper = mode.upper()
        if mode_upper == "GENERAL":
            return random.randint(7200, 10800)
        elif mode_upper == "JOURNEY":
            if estimated_duration_minutes <= 0:
                estimated_duration_minutes = 30
            total_seconds = estimated_duration_minutes * 60
            num_checkins = random.choice([2, 3])
            segment_seconds = total_seconds / num_checkins
            jitter = segment_seconds * 0.2
            interval = random.uniform(segment_seconds - jitter, segment_seconds + jitter)
            return max(60, int(interval))
        return 60

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
        
        ttl_seconds = await self.calculate_next_interval(mode, estimated_duration_minutes)

        session_data = {
            "child_id": child_id,
            "mode": mode,
            "safe_code_hash": safe_code_hash,
            "duress_code_hash": duress_code_hash,
            "parent_contacts": parent_contacts,
            "estimated_duration_minutes": estimated_duration_minutes,
            "status": "ACTIVE",
            "retry_count": 0
        }
        
        await self.redis_client.set(session_key, json.dumps(session_data))
        await self.redis_client.setex(timer_key, ttl_seconds, "TICKING")
        
        logger.info(f"Safety tracking ({mode}) spawned for child {child_id}. Interval set to {ttl_seconds}s.")
        return True

    async def verify_user_code(self, child_id: str, plain_code: str) -> Dict[str, Any]:
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        response_timer_key = f"periodic:response:{child_id}"

        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return {"status": "ERROR", "message": "No active safety session found."}

        session_data = json.loads(raw_session)
        stored_safe_hash = session_data.get("safe_code_hash", "")
        stored_duress_hash = session_data.get("duress_code_hash", "")

        def verify_hash(plain: str, hashed: str) -> bool:
            if not hashed:
                return False
            try:
                if hashed.startswith("$2a$") or hashed.startswith("$2b$") or hashed.startswith("$2y$"):
                    return pwd_context.verify(plain, hashed)
                return plain == hashed
            except Exception as e:
                logger.error(f"PIN verification error: {e}")
                return plain == hashed

        if verify_hash(plain_code, stored_safe_hash):
            await self.redis_client.delete(response_timer_key, timer_key)
            next_interval = await self.calculate_next_interval(
                session_data.get("mode", "GENERAL"), 
                session_data.get("estimated_duration_minutes", 0)
            )
            session_data["status"] = "ACTIVE"
            session_data["retry_count"] = 0

            await self.redis_client.set(session_key, json.dumps(session_data))
            await self.redis_client.setex(timer_key, next_interval, "TICKING")
            logger.info(f"Child {child_id} SAFE. Timer restarted and retries reset.")

            return {"status": "SUCCESS", "message": "Safety confirmed. Next check started."}

        if verify_hash(plain_code, stored_duress_hash):
            logger.warning(f"DURESS PIN entered by {child_id}")
            await self.trigger_emergency_alert(
                child_id=child_id,
                target_contacts=session_data.get("parent_contacts", []),
                reason="DURESS_TRIGGERED"
            )
            await self.redis_client.delete(timer_key, response_timer_key, session_key)
            return {"status": "DURESS", "message": "Emergency alert triggered."}

        return {"status": "INVALID_CODE", "message": "Incorrect safety code."}

    async def trigger_emergency_alert(self, child_id: str, target_contacts: List[str], reason: str):
        alert_payload = {
            "event": "EMERGENCY_SOS",
            "type": "PARENT_ALERT",
            "child_id": child_id,
            "reason": reason,
            "recipients": target_contacts,
            "title": "🚨 EMERGENCY SOS: Safety Check Ignored",
            "message": "ShieldX Security Alert: Your child failed to respond to all safety check-in retries!"
        }
        await self.redis_client.publish("notification_channel_stream", json.dumps(alert_payload))
        logger.info(f"Emergency SOS payload dispatched to parents for child {child_id}")

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
            "retry_count": session_data.get("retry_count", 0),
            "mode": session_data.get("mode"),
            "remaining_seconds": max(remaining_seconds, 0)
        }

    async def stop_safety_session(self, child_id: str) -> Dict[str, Any]:
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        response_timer_key = f"periodic:response:{child_id}"

        if not await self.redis_client.exists(session_key):
            return {"status": "NOT_FOUND", "message": "No active safety session found."}

        await self.redis_client.delete(session_key, timer_key, response_timer_key, f"periodic:lock:{child_id}")
        logger.info(f"Periodic safety session stopped for child {child_id}")
        return {"status": "SUCCESS", "message": "Periodic safety session stopped successfully."}

    async def send_checkin_request(self, child_id: str) -> None:
        session_key = f"periodic:session:{child_id}"
        lock_key = f"periodic:lock:{child_id}"
        
        acquired = await self.redis_client.set(lock_key, "locked", nx=True, ex=3)
        if not acquired:
            return
        
        response_timer_key = f"periodic:response:{child_id}"

        try:
            raw_session = await self.redis_client.get(session_key)
            if not raw_session:
                return

            session_data = json.loads(raw_session)
            retry_count = session_data.get("retry_count", 0)

            if retry_count >= self.MAX_RETRIES:
                await self.trigger_emergency_alert(
                    child_id=child_id,
                    target_contacts=session_data.get("parent_contacts", []),
                    reason="MAX_RETRIES_EXCEEDED"
                )
                session_data["status"] = "EMERGENCY_SOS"
                await self.redis_client.set(session_key, json.dumps(session_data))
                return

            retry_count += 1
            session_data["retry_count"] = retry_count
            session_data["status"] = "CHALLENGED"
            await self.redis_client.set(session_key, json.dumps(session_data))

            await self.redis_client.setex(response_timer_key, 60, "WAITING_FOR_RESPONSE")

            payload = {
                "event": "PERIODIC_CHECKIN",
                "type": "SAFETY_CHALLENGE",
                "child_id": child_id,
                "recipients": [child_id],
                "title": f"🛡️ ShieldX Safety Check ({retry_count}/{self.MAX_RETRIES})",
                "message": "Are you safe? Tap here to enter your security PIN."
            }

            await self.redis_client.publish("notification_channel_stream", json.dumps(payload))
            logger.info(f"Check-in attempt {retry_count} sent for {child_id}")
        finally:
            pass

    async def handle_no_response(self, child_id: str):
        session_key = f"periodic:session:{child_id}"
        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return

        session_data = json.loads(raw_session)
        retry_count = session_data.get("retry_count", 0)

        if retry_count < self.MAX_RETRIES:
            await self.send_checkin_request(child_id)
        else:
            await self.trigger_emergency_alert(
                child_id=child_id,
                target_contacts=session_data.get("parent_contacts", []),
                reason="NO_RESPONSE_MAX_RETRIES"
            )
            session_data["status"] = "EMERGENCY_SOS"
            await self.redis_client.set(session_key, json.dumps(session_data))
            await self.redis_client.delete(session_key, f"periodic:response:{child_id}")