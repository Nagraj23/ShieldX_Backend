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
            response_timer_key = f"periodic:response:{child_id}"
            await self.redis_client.delete(response_timer_key)
            # Clear out the current expired timer key and push a brand new cycle countdown
            ttl_seconds = int(session_data["interval_minutes"]) * 60
            await self.redis_client.setex(timer_key, ttl_seconds, "TICKING")
            
            logger.info(f"Child {child_id} verified SAFE. Timer loop reset.")
            return {"status": "SUCCESS", "message": "All clear received. Next countdown loop initialized."}
            
        # Match Step B: Check if it's the high-priority Duress Code
        elif pwd_context.verify(plain_code, session_data["duress_code_hash"]):
            logger.warning(f"CRITICAL: Child {child_id} entered silent DURESS PIN! Triggering fallback system...")
            
            response_timer_key = f"periodic:response:{child_id}"
            await self.redis_client.delete(response_timer_key)
            # Immediately fire the alert payload to the notification tier
            await self.trigger_emergency_alert(child_id, session_data["parent_contacts"], reason="DURESS_TRIGGERED")
            
            await self.redis_client.delete(timer_key)
            await self.redis_client.delete(response_timer_key)
            await self.redis_client.delete(session_key)
            # Clear tracking variables from cache to shut down the cycle
            await self.redis_client.delete(timer_key)
            await self.redis_client.delete(session_key)
            
            response_timer_key = f"periodic:response:{child_id}"
            await self.redis_client.delete(response_timer_key)
            
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
        
    async def get_session_status(self, child_id: str) -> Dict[str, Any]:
        """
        Returns the current status of an active periodic safety session.
        """

        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"

        # Check whether an active session exists
        raw_session = await self.redis_client.get(session_key)

        if not raw_session:
            return {
                "status": "NOT_FOUND",
                "message": "No active safety session found."
            }

        # Load cached session data
        session_data = json.loads(raw_session)

        # Fetch remaining TTL of the active timer
        remaining_seconds = await self.redis_client.ttl(timer_key)

        # Handle edge cases where timer no longer exists
        if remaining_seconds < 0:
            remaining_seconds = 0

        return {
            "status": session_data.get("status", "ACTIVE"),
            "child_id": child_id,
            "interval_minutes": session_data.get("interval_minutes"),
            "remaining_seconds": remaining_seconds
        }
    async def stop_safety_session(self, child_id: str) -> Dict[str, Any]:
        """
        Stops an active periodic safety session by removing all related Redis keys.
        """

        session_key = f"periodic:session:{child_id}"
        timer_key = f"periodic:timer:{child_id}"

        # Check if session exists
        if not await self.redis_client.exists(session_key):
            return {
                "status": "NOT_FOUND",
                "message": "No active safety session found."
            }

        # Delete session and timer
        await self.redis_client.delete(session_key)
        await self.redis_client.delete(timer_key)

        logger.info(f"Periodic safety session stopped for child {child_id}")

        return {
            "status": "SUCCESS",
            "message": "Periodic safety session stopped successfully."
        }
        
    async def send_checkin_request(
    self,
        child_id: str,
        parent_contacts: List[str]
    ) -> None:
        """
        Publishes a periodic safety check-in request to the Notification Service.
        """

        checkin_payload = {
            "event": "PERIODIC_CHECKIN",
            "child_id": child_id,
            "recipients": parent_contacts,
            "title": "ShieldX Safety Check",
            "message": "Are you safe? Please enter your safety code within 30 seconds."
        }

        channel = "notification_channel_stream"

        await self.redis_client.publish(
            channel,
            json.dumps(checkin_payload)
        )

        logger.info(
            f"Periodic check-in published for child {child_id}"
        )
    async def handle_no_response(
    self,
        child_id: str,
        target_contacts: List[str]
    ):
        """
        Handles the case where the user fails to respond to the periodic safety check-in.
        """

        logger.warning(
            f"No response received from child {child_id}. Triggering emergency alert."
        )

        # Trigger the emergency notification
        await self.trigger_emergency_alert(
            child_id=child_id,
            target_contacts=target_contacts,
            reason="NO_RESPONSE"
        )

        # Clean up Redis keys
        session_key = f"periodic:session:{child_id}"
        response_timer_key = f"periodic:response:{child_id}"

        await self.redis_client.delete(session_key)
        await self.redis_client.delete(response_timer_key)

        logger.info(
            f"Periodic safety session cleaned up for child {child_id}"
        )
    
    async def retry_checkin(
        self,
        child_id: str,
        parent_contacts: List[str]
    ) -> None:
        """
        Sends another periodic safety check-in request after a missed response
        and restarts the response timer.
        """

        retry_key = f"periodic:retry:{child_id}"
        response_timer_key = f"periodic:response:{child_id}"

        # Read current retry count
        retry_count = await self.redis_client.get(retry_key)

        if retry_count is None:
            retry_count = 0
        else:
            retry_count = int(retry_count)

        # Increment retry count
        retry_count += 1

        await self.redis_client.set(retry_key, retry_count)

        logger.warning(
            f"Retrying periodic safety check-in for child {child_id}. Attempt #{retry_count}"
        )

        # Send another check-in notification
        await self.send_checkin_request(
            child_id=child_id,
            parent_contacts=parent_contacts
        )

        # Restart the 30-second response timer
        await self.redis_client.setex(
            response_timer_key,
            30,
            "WAITING_FOR_RESPONSE"
        )