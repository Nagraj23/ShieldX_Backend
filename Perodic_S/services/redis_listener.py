import asyncio
import logging
from config.redis_config import get_redis_client
from services.safety_service import SafetyService

logger = logging.getLogger("redis_listener")
safety_service = SafetyService()

RESPONSE_TIMEOUT = 60  # 1 minute window for response
MAX_RETRIES = 3        # Configurable: retry 3 to 5 times before parent SOS

async def listen_to_timer_expirations():
    redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    channel = "__keyevent@0__:expired"

    await pubsub.subscribe(channel)
    logger.info(f"🟢 [Redis Listener] Subscribed to keyspace expiry channel: {channel}")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1
            )

            if message:
                expired_key = message["data"]

                if isinstance(expired_key, bytes):
                    expired_key = expired_key.decode()

                if expired_key.startswith("periodic:timer:"):
                    child_id = expired_key.replace("periodic:timer:", "")
                    session_key = f"periodic:session:{child_id}"
                    response_key = f"periodic:response:{child_id}"

                    if not await redis_client.exists(session_key):
                        continue

                    # Trigger single check-in alert
                    await safety_service.send_checkin_request(child_id)

                    # Start the 1-minute response grace period window
                    await redis_client.setex(
                        response_key,
                        RESPONSE_TIMEOUT,
                        "WAITING"
                    )

                    logger.warning(f"⚠️ [Check-In Sent] Initial alert sent for child {child_id}")

                # ==========================================
                # 2. RESPONSE WINDOW EXPIRED (Handle Retry / SOS)
                # ==========================================
                elif expired_key.startswith("periodic:response:"):
                    child_id = expired_key.replace("periodic:response:", "")
                    session_key = f"periodic:session:{child_id}"
                    retry_key = f"periodic:retry:{child_id}"
                    response_key = f"periodic:response:{child_id}"

                    # If session was stopped or redeemed (user entered pin), ignore expiration
                    if not await redis_client.exists(session_key):
                        await redis_client.delete(retry_key)
                        continue

                    retry = await redis_client.get(retry_key)
                    retry = int(retry or 0)

                    if retry < MAX_RETRIES:
                        # Increment retry count
                        new_retry_count = retry + 1
                        await redis_client.set(retry_key, new_retry_count)

                        # Resend ONLY ONE check-in alert
                        await safety_service.send_checkin_request(child_id)

                        # Reset the 1-minute response timer for the next attempt
                        await redis_client.setex(
                            response_key,
                            RESPONSE_TIMEOUT,
                            "WAITING"
                        )

                        logger.warning(f"🔄 [Retry Sent] Attempt {new_retry_count}/{MAX_RETRIES} sent for child {child_id}")

                    else:
                        # Max retries exhausted! Finalize and trigger Parent SOS alert
                        await safety_service.handle_no_response(child_id)

                        await redis_client.delete(
                            session_key,
                            retry_key,
                            response_key
                        )

                        logger.error(f"🚨 [SOS Triggered] Child {child_id} failed to respond after {MAX_RETRIES} retries. Parents alerted.")

            await asyncio.sleep(0.1)

    except Exception as e:
        logger.exception(f"❌ Redis keyspace listener crashed: {e}")

    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()