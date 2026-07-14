import json
import time
import logging
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger("ShieldX.Redis")

redis_client = aioredis.from_url(
    settings.redis_url,
    decode_responses=True
)


class RedisPubSubService:

    PRESENCE_TTL_SECONDS = 45

    @staticmethod
    def get_user_channel(user_id: str) -> str:
        return f"notification:user:{user_id}"

    @staticmethod
    def get_presence_key(user_id: str) -> str:
        return f"user:{user_id}:presence"

    @staticmethod
    async def track_heartbeat(
        user_id: str,
        fcm_token: Optional[str] = None
    ) -> None:

        try:
            key = RedisPubSubService.get_presence_key(user_id)

            mapping = {
                "last_seen_ts": str(time.time()),
                "is_online": "true"
            }

            if fcm_token:
                mapping["fcm_token"] = fcm_token

            async with redis_client.pipeline(transaction=True) as pipe:
                await pipe.hset(key, mapping=mapping)
                await pipe.expire(
                    key,
                    RedisPubSubService.PRESENCE_TTL_SECONDS
                )
                await pipe.execute()

        except Exception as e:
            logger.error(
                f"Heartbeat tracking failed for user {user_id}: {e}"
            )

    @staticmethod
    async def get_user_reachability(
        user_id: str
    ) -> Dict[str, Any]:

        try:
            key = RedisPubSubService.get_presence_key(user_id)

            data = await redis_client.hgetall(key)

            if not data:
                return {
                    "is_online": False,
                    "fcm_token": None
                }

            return {
                "is_online": data.get("is_online") == "true",
                "fcm_token": data.get("fcm_token")
            }

        except Exception as e:
            logger.error(
                f"Presence lookup failed for user {user_id}: {e}"
            )

            return {
                "is_online": False,
                "fcm_token": None
            }

    @staticmethod
    async def publish_to_user(
        user_id: str,
        payload: Dict[str, Any]
    ) -> bool:

        try:
            channel = RedisPubSubService.get_user_channel(user_id)

            subscribers = await redis_client.pubsub_numsub(channel)

            listener_count = (
                subscribers[0][1]
                if subscribers
                else 0
            )

            if listener_count <= 0:
                logger.info(
                    f"No active subscribers for user {user_id}"
                )
                return False

            await redis_client.publish(
                channel,
                json.dumps(payload, default=str)
            )

            logger.info(
                f"Notification published to user {user_id}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Redis publish failed for user {user_id}: {e}"
            )
            return False