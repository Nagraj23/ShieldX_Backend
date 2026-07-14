import asyncio
import logging
from typing import Any, Dict

from firebase_admin import messaging
from twilio.rest import Client

from config import settings

logger = logging.getLogger("ShieldX.Notification")

twilio_client = (
    Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN
    else None
)


class FallbackNotificationService:

    @staticmethod
    async def dispatch_fcm_push(
        fcm_token: str,
        title: str,
        body: str,
        data_payload: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not fcm_token:
            return {
                "success": False,
                "provider": "FCM",
                "code": 400,
                "reason": "Missing FCM token"
            }

        try:

            sanitized_payload = {
                str(k): str(v)
                for k, v in data_payload.items()
            }

            message = messaging.Message(
                token=fcm_token,
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=sanitized_payload,
                android=messaging.AndroidConfig(
                    priority="high"
                )
            )

            loop = asyncio.get_running_loop()

            response = await loop.run_in_executor(
                None,
                messaging.send,
                message
            )

            logger.info(
                f"FCM notification delivered successfully."
            )

            return {
                "success": True,
                "provider": "FCM",
                "code": 200,
                "response_id": response
            }

        except Exception as e:

            logger.exception("FCM delivery failed")

            return {
                "success": False,
                "provider": "FCM",
                "code": 500,
                "reason": str(e)
            }

    @staticmethod
    async def dispatch_twilio_sms(
        phone_number: str,
        message_body: str
    ) -> Dict[str, Any]:

        if not twilio_client:
            return {
                "success": False,
                "provider": "TWILIO",
                "code": 500,
                "reason": "Twilio is not configured."
            }

        if not phone_number:
            return {
                "success": False,
                "provider": "TWILIO",
                "code": 400,
                "reason": "Missing phone number."
            }

        try:

            loop = asyncio.get_running_loop()

            sms = await loop.run_in_executor(
                None,
                lambda: twilio_client.messages.create(
                    body=message_body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
            )

            logger.info(
                f"SMS delivered successfully."
            )

            return {
                "success": True,
                "provider": "TWILIO",
                "code": 200,
                "sid": sms.sid
            }

        except Exception as e:

            logger.exception("Twilio SMS delivery failed")

            return {
                "success": False,
                "provider": "TWILIO",
                "code": 500,
                "reason": str(e)
            }