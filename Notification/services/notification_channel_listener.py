import asyncio
import json
import logging

from services.redis_pubsub import redis_client, publish_to_user

logger = logging.getLogger("ShieldX.NotificationListener")


async def listen_notification_stream():
    pubsub = redis_client.pubsub()

    await pubsub.subscribe("notification_channel_stream")

    logger.info("Subscribed to notification_channel_stream")

    while True:
        try:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0
            )

            if message:
                payload = json.loads(message["data"])

                child_id = payload.get("child_id")

                if child_id:
                    await publish_to_user(
                        child_id,
                        payload
                    )

                    logger.info(
                        f"Forwarded notification to user {child_id}"
                    )

            await asyncio.sleep(0.1)

        except Exception as e:
            logger.exception(
                f"Notification stream listener failed: {e}"
            )