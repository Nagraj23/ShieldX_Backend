import json
import logging
from typing import Dict, Any, List
from passlib.context import CryptContext
from config.redis_config import get_redis_client

# Initialize Passlib context with Bcrypt to match your Java configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger("safety_service")

class SafetyService:
    def __init__(self):
        self.redis_client = get_redis_client()

    async def start_safety_session(
        self, 
        child_id: str, 
        interval_minutes: int, 
        safe_code_hash: str, 
        duress_code_hash: str, 
        parent_contacts: List[str]
    ) -> bool:
        """
        Initializes the session configuration and registers the ticking countdown in Redis.
        """
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        
        session_data = {
            "child_id": child_id,
            "safe_code_hash": safe_code_hash,
            "duress_code_hash": duress_code_hash,
            "parent_contacts": parent_contacts,
            "interval_minutes": interval_minutes,
            "status": "ACTIVE"
        }
        
        # 1. Store the baseline safety metadata session parameters (No expiration time)
        await self.redis_client.set(session_key, json.dumps(session_data))
        
        # 2. Start the primary tracking timer using Redis Key Time-To-Live (in seconds)
        ttl_seconds = interval_minutes * 60
        await self.redis_client.setex(timer_key, ttl_seconds, "TICKING")
        
        logger.info(f"Safety tracking successfully spawned for child {child_id}. Interval: {interval_minutes}m")
        return True

    async def verify_user_code(self, child_id: str, plain_code: str) -> Dict[str, Any]:
        """
        Verifies the user entered string against the saved safe and duress hashes.
        """
        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"
        
        # Pull down the stored session variables
        raw_session = await self.redis_client.get(session_key)
        if not raw_session:
            return {"status": "ERROR", "message": "No active safety tracking found for this user context."}
            
        session_data = json.loads(raw_session)
        print("=" * 50)
        print("Plain Code:", repr(plain_code))
        print("Plain Code Type:", type(plain_code))
        print("Plain Code Length:", len(plain_code))

        print("Safe Hash:", repr(session_data["safe_code_hash"]))
        print("Safe Hash Type:", type(session_data["safe_code_hash"]))
        print("Safe Hash Length:", len(session_data["safe_code_hash"]))
        print("=" * 50)
        
        # Match Step A: Check if it's the valid Safe Code
        if pwd_context.verify(plain_code, session_data["safe_code_hash"]):
            # Clear out the current expired timer key and push a brand new cycle countdown
            ttl_seconds = int(session_data["interval_minutes"]) * 60
            await self.redis_client.setex(timer_key, ttl_seconds, "TICKING")
            
            logger.info(f"Child {child_id} verified SAFE. Timer loop reset.")
            return {"status": "SUCCESS", "message": "All clear received. Next countdown loop initialized."}
            
        # Match Step B: Check if it's the high-priority Duress Code
        elif pwd_context.verify(plain_code, session_data["duress_code_hash"]):
            logger.warning(f"CRITICAL: Child {child_id} entered silent DURESS PIN! Triggering fallback system...")
            
            # Immediately fire the alert payload to the notification tier
            await self.trigger_emergency_alert(child_id, session_data["parent_contacts"], reason="DURESS_TRIGGERED")
            
            # Clear tracking variables from cache to shut down the cycle
            await self.redis_client.delete(timer_key)
            await self.redis_client.delete(session_key)
            
            # Mask the return payload on the client UI so an attacker thinks it was a success!
            return {"status": "SUCCESS", "message": "All clear received. Next countdown loop initialized."}
            
        # Match Step C: Plain digits matched absolutely nothing
        else:
            return {"status": "INVALID_CODE", "message": "Incorrect combination entered. Please verify and try again."}

    async def trigger_emergency_alert(self, child_id: str, target_contacts: List[str], reason: str):
        """
        Formats and publishes the alert payload straight to the notification service messaging stream channel.
        """
        alert_payload = {
            "event": "SAFETY_ALERT_SOS",
            "child_id": child_id,
            "reason": reason,
            "recipients": target_contacts,
            "message": "ShieldX Security Alert: Your child failed their check-in prompt or entered a duress code. Immediate verification required."
        }
        
        # Publish to your central Redis notification pipe channel
        channel_pipe = "notification_channel_stream"
        await self.redis_client.publish(channel_pipe, json.dumps(alert_payload))
        logger.info(f"Emergency payload dispatched across channel '{channel_pipe}' for child {child_id}")