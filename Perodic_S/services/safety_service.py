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
        self.MAX_RETRIES = 3  # Target retry limit before parental escalation

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
            "status": "ACTIVE",
            "retry_count": 0  # 🛡️ Track current retry attempt
        }
        
        await self.redis_client.set(session_key, json.dumps(session_data))
        await self.redis_client.setex(timer_key, ttl_seconds, "TICKING")
        
        logger.info(f"Safety tracking ({mode}) spawned for child {child_id}. Interval set to {interval_minutes}m.")
        return True

    async def verify_user_code(
            self,
            child_id: str,
            plain_code: str
        ) -> Dict[str, Any]:

            session_key = f"periodic:session:{child_id}"
            timer_key = f"periodic:timer:{child_id}"
            response_timer_key = f"periodic:response:{child_id}"

            raw_session = await self.redis_client.get(session_key)

            if not raw_session:
                return {
                    "status": "ERROR",
                    "message": "No active safety session found."
                }

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

            # ============================
            # SAFE CODE (Success & Reset)
            # ============================
            if verify_hash(plain_code, stored_safe_hash):
                # Clear all active timeout/response keys and reset retry count
                await self.redis_client.delete(response_timer_key, timer_key)

                interval_seconds = int(session_data.get("interval_minutes", 1)) * 60

                session_data["status"] = "ACTIVE"
                session_data["retry_count"] = 0  # Reset retry counter on success

                await self.redis_client.set(session_key, json.dumps(session_data))
                await self.redis_client.setex(timer_key, interval_seconds, "TICKING")

                logger.info(f"Child {child_id} SAFE. Timer restarted and retries reset.")

                return {
                    "status": "SUCCESS",
                    "message": "Safety confirmed. Next check started."
                }

            # ============================
            # DURESS CODE
            # ============================
            if verify_hash(plain_code, stored_duress_hash):
                logger.warning(f"DURESS PIN entered by {child_id}")
                await self.trigger_emergency_alert(
                    child_id=child_id,
                    target_contacts=session_data.get("parent_contacts", []),
                    reason="DURESS_TRIGGERED"
                )
                await self.redis_client.delete(timer_key, response_timer_key, session_key)

                return {
                    "status": "DURESS",
                    "message": "Emergency alert triggered."
                }

            # ============================
            # INVALID PIN
            # ============================
            return {
                "status": "INVALID_CODE",
                "message": "Incorrect safety code."
            }

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
        channel_pipe = "notification_channel_stream"
        await self.redis_client.publish(channel_pipe, json.dumps(alert_payload))
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
            "interval_minutes": session_data.get("interval_minutes"),
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
        
        # 🔒 Safe Atomic Lock with a clean 3-second window
        acquired = await self.redis_client.set(lock_key, "locked", nx=True, ex=3)
        if not acquired:
            logger.warning(f"Duplicate expiry event suppressed via lock for {child_id}")
            return
        
        response_timer_key = f"periodic:response:{child_id}"

        try:
            raw_session = await self.redis_client.get(session_key)
            if not raw_session:
                return

            session_data = json.loads(raw_session)
            retry_count = session_data.get("retry_count", 0)

            # Check if max retries have been exhausted
            if retry_count >= self.MAX_RETRIES:
                logger.warning(f"Max retries ({self.MAX_RETRIES}) reached for {child_id}. Triggering SOS.")
                await self.trigger_emergency_alert(
                    child_id=child_id,
                    target_contacts=session_data.get("parent_contacts", []),
                    reason="MAX_RETRIES_EXCEEDED"
                )
                session_data["status"] = "EMERGENCY_SOS"
                await self.redis_client.set(session_key, json.dumps(session_data))
                return

            # Increment retry counter and update session status to CHALLENGED
            retry_count += 1
            session_data["retry_count"] = retry_count
            session_data["status"] = "CHALLENGED"
            await self.redis_client.set(session_key, json.dumps(session_data))

            # Set a 1-minute response grace period timer for this specific attempt
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
            logger.info(f"✅ Check-in attempt {retry_count} sent and published. Status successfully set to CHALLENGED for {child_id}")

        finally:
            # Keep the lock for a brief moment or release it depending on your flow
            pass

    async def handle_no_response(self, child_id: str):
        """
        Called when the 1-minute response TTL (periodic:response:{child_id}) expires 
        without the user entering a code. It triggers another retry or escalates.
        """
        session_key = f"periodic:session:{child_id}"
        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return

        session_data = json.loads(raw_session)
        retry_count = session_data.get("retry_count", 0)

        if retry_count < self.MAX_RETRIES:
            logger.info(f"Child {child_id} missed response window. Triggering retry attempt {retry_count + 1}...")
            await self.send_checkin_request(child_id)
        else:
            logger.warning(f"Child {child_id} failed all {self.MAX_RETRIES} attempts. Finalizing emergency SOS.")
            await self.trigger_emergency_alert(
                child_id=child_id,
                target_contacts=session_data.get("parent_contacts", []),
                reason="NO_RESPONSE_MAX_RETRIES"
            )
            session_data["status"] = "EMERGENCY_SOS"
            await self.redis_client.set(session_key, json.dumps(session_data))
            await self.redis_client.delete(session_key, f"periodic:response:{child_id}")