import logging
import asyncio
from typing import Dict, Any
from firebase_admin import messaging
from twilio.rest import Client
from config import settings

logger = logging.getLogger("ShieldX.FallbackEngine")
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN) if (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN) else None

class FallbackNotificationService:
    @staticmethod
    async def dispatch_fcm_push(fcm_token: str, title: str, body: str, data_payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            sanitized_data = {k: str(v) for k, v in data_payload.items()}
            message = messaging.Message(
                token=fcm_token,
                notification=messaging.Notification(title=title, body=body),
                data=sanitized_data,
                android=messaging.AndroidConfig(priority="high")
            )
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, messaging.send, message)
            return {"success": True, "code": 200, "response_id": response}
        except Exception as e:
            logger.error(f"FCM failure: {e}")
            return {"success": False, "code": 500, "reason": str(e)}

    @staticmethod
    async def dispatch_twilio_sms(phone_number: str, message_body: str) -> Dict[str, Any]:
        if not twilio_client: return {"success": False, "code": 500, "reason": "Twilio Unconfigured"}
        try:
            loop = asyncio.get_running_loop()
            msg = await loop.run_in_executor(
                None, lambda: twilio_client.messages.create(body=message_body, from_=settings.TWILIO_PHONE_NUMBER, to=phone_number)
            )
            return {"success": True, "code": 200, "sid": msg.sid}
        except Exception as e:
            return {"success": False, "code": 500, "reason": str(e)}