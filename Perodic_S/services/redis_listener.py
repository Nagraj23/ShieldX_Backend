import asyncio
import json
import logging
from config.redis_config import get_redis_client
from services.safety_service import SafetyService

logger = logging.getLogger("redis_listener")
safety_service = SafetyService()

async def listen_to_timer_expirations():
    """
    Asynchronous background event monitor loop listening exclusively for Redis key eviction events.
    Fires the Dead-Man's Switch alert down the event stream without touching a database.
    """
    redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    
    # Listen for expirations on Redis Database index 0
    expiration_channel = "__keyevent@0__:expired"
    await pubsub.subscribe(expiration_channel)
    
    logger.info(f"Asynchronous Redis Keyspace Listener actively polling: {expiration_channel}")
    
    try:
        while True:
            # Poll for key changes in memory
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            
            if message:
                expired_key = message['data']
                
                # Check if the evicted key string maps to our periodic safety timers
                if expired_key.startswith("periodic:timer:"):
                    child_id = expired_key.replace("periodic:timer:", "")
                    logger.error(f"🔴 DEAD-MAN'S SWITCH: Child {child_id} missed their safety check-in!")
                    
                    # Fetch tracking metadata stored securely in the Redis session cache envelope
                    session_key = f"periodic:session:{child_id}"
                    raw_session = await redis_client.get(session_key)
                    
                    if raw_session:
                        session_data = json.loads(raw_session)
                        parent_ids = session_data.get("parent_contacts", [])
                        
                        # Build the clear payload containing parent IDs for the Notification Service to handle
                        alert_payload = {
                            "type": "EMERGENCY_SOS",
                            "feature": "PERIODIC_SAFETY",
                            "child_id": child_id,
                            "reason": "TIMEOUT_EXPIRED",
                            "target_parents": parent_ids,  # Array of parent UUIDs read directly from cache
                            "title": "🔴 SHIELDX EMERGENCY ALERT",
                            "message": "ShieldX System Alert: Your child failed to check in within the safety window."
                        }
                        
                        # Drop the payload directly into the decoupled notification broker pipe
                        channel_pipe = "notification_channel_stream"
                        await redis_client.publish(channel_pipe, json.dumps(alert_payload))
                        logger.warning(f"Emergency event published to stream '{channel_pipe}' for parent IDs: {parent_ids}")
                        
                        # Evict residual metadata out of memory cache
                        await redis_client.delete(session_key)
                        
            # Short yield to prevent CPU thread starvation
            await asyncio.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Critical error inside the background monitor layer: {str(e)}")
    finally:
        await pubsub.unsubscribe(expiration_channel)
        await redis_client.close()