import logging

from rq.exceptions import Retry

from config import settings
from db import (
    get_notification,
    update_notification_status,
)
from services.redis_pubsub import RedisPubSubService
from fcm import FallbackNotificationService
from models.notification_model import DeliveryAttempt

logger = logging.getLogger("ShieldX.Worker")


async def execute_delivery(notification_id: str):

    notification = await get_notification(notification_id)

    if not notification:
        return {"status": "NOT_FOUND"}

    history = notification.get("status_history", [])

    attempt_number = len(history) + 1

    recipients = notification.get("recipients", [])

    payload = notification.get("payload", {})

    notification_data = notification.get("notification", {})

    title = notification_data.get("title", "ShieldX Notification")

    body = notification_data.get("body", "")

    overall_success = True

    delivered_channel = None

    for recipient in recipients:

        user_id = recipient.get("id")

        if not user_id:
            continue

        recipient_success = False

        # ----------------------------------------------------
        # Tier 1 : Redis PubSub
        # ----------------------------------------------------

        if await RedisPubSubService.publish_to_user(
            user_id,
            payload
        ):

            recipient_success = True

            delivered_channel = "REDIS_PUBSUB"

            attempt = DeliveryAttempt(
                channel="REDIS_PUBSUB",
                result="SUCCESS",
                attempt_number=attempt_number
            )

            await update_notification_status(
                notification_id,
                {},
                attempt.model_dump()
            )

        else:

            # ------------------------------------------------
            # Tier 2 : Firebase Push
            # ------------------------------------------------

            reachability = await RedisPubSubService.get_user_reachability(
                user_id
            )

            token = reachability.get("fcm_token")

            if token:

                result = await FallbackNotificationService.dispatch_fcm_push(
                    token,
                    title,
                    body,
                    payload
                )

                if result["success"]:

                    recipient_success = True

                    delivered_channel = "FCM_PUSH"

                    attempt = DeliveryAttempt(
                        channel="FCM_PUSH",
                        result="SUCCESS",
                        attempt_number=attempt_number,
                        provider_response=result
                    )

                    await update_notification_status(
                        notification_id,
                        {},
                        attempt.model_dump()
                    )

            # ------------------------------------------------
            # Tier 3 : SMS
            # ------------------------------------------------

            if not recipient_success:

                phone = recipient.get("phone")

                if phone:

                    result = await FallbackNotificationService.dispatch_twilio_sms(
                        phone,
                        body
                    )

                    if result["success"]:

                        recipient_success = True

                        delivered_channel = "TWILIO_SMS"

                        attempt = DeliveryAttempt(
                            channel="TWILIO_SMS",
                            result="SUCCESS",
                            attempt_number=attempt_number,
                            provider_response=result
                        )

                        await update_notification_status(
                            notification_id,
                            {},
                            attempt.model_dump()
                        )

        if not recipient_success:

            overall_success = False

            attempt = DeliveryAttempt(
                channel="REDIS_PUBSUB",
                result="FAILED_TRANSIENT",
                attempt_number=attempt_number
            )

            await update_notification_status(
                notification_id,
                {},
                attempt.model_dump()
            )

    # --------------------------------------------------------
    # Final Status
    # --------------------------------------------------------

    if overall_success:

        await update_notification_status(
            notification_id,
            {
                "delivered": True,
                "delivered_via": delivered_channel,
                "final_status": "COMPLETED"
            }
        )

        return {
            "status": "SUCCESS"
        }

    # --------------------------------------------------------
    # Retry
    # --------------------------------------------------------

    if attempt_number < settings.MAX_DELIVERY_ATTEMPTS:

        delay = (
            settings.INITIAL_RETRY_DELAY_SECONDS
            * (2 ** (attempt_number - 1))
        )

        raise Retry(delay=delay)

    await update_notification_status(
        notification_id,
        {
            "delivered": False,
            "final_status": "FAILED"
        }
    )

    return {
        "status": "FAILED"
    }