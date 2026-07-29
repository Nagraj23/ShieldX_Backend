import asyncio
import json
import logging
from config.redis_config import get_redis_client
from services.safety_service import SafetyService

logger = logging.getLogger("redis_listener")
safety_service = SafetyService()

async def listen_to_timer_expirations():
    redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    
    expiration_channel = "__keyevent@0__:expired"
    await pubsub.subscribe(expiration_channel)
    
    logger.info(f"Asynchronous Redis Keyspace Listener actively polling: {expiration_channel}")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            
            if message:
                expired_key = message['data']
                
                # 1. Main Periodic Timer Expired (e.g., after 1 min test)
                if expired_key.startswith("periodic:timer:"):
                    child_id = expired_key.replace("periodic:timer:", "")
                    logger.error(f"🔴 DEAD-MAN'S SWITCH: Child {child_id} missed their safety check-in!")
                    
                    # This method inside SafetyService sets status to CHALLENGED 
                    # and publishes to Redis channel "notification_channel_stream"
                    await safety_service.send_checkin_request(child_id=child_id)
                    
                    response_timer_key = f"periodic:response:{child_id}"
                    retry_key = f"periodic:retry:{child_id}"

                    await redis_client.set(retry_key, 0)
                    await redis_client.setex(response_timer_key, 30, "WAITING_FOR_RESPONSE")
                    
                # 2. 30-Second Response Window Expired
                elif expired_key.startswith("periodic:response:"):
                    child_id = expired_key.replace("periodic:response:", "")
                    logger.warning(f"No response received for periodic safety check-in from child {child_id}")

                    session_key = f"periodic:session:{child_id}"
                    retry_key = f"periodic:retry:{child_id}"

                    raw_session = await redis_client.get(session_key)

                    if raw_session:
                        retry_count = await redis_client.get(retry_key)
                        retry_count = int(retry_count) if retry_count else 0

                        if retry_count < 2:
                            await redis_client.incr(retry_key)
                            await safety_service.send_checkin_request(child_id=child_id)
                            await redis_client.setex(f"periodic:response:{child_id}", 30, "WAITING_FOR_RESPONSE")
                        else:
                            # Final failure: Trigger SOS Emergency Alert via Redis publish
                            await safety_service.handle_no_response(child_id=child_id)
                            await redis_client.delete(session_key, f"periodic:response:{child_id}", retry_key)
                        
            await asyncio.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Critical error inside background layer: {str(e)}")
    finally:
        await pubsub.unsubscribe(expiration_channel)
        await redis_client.close()