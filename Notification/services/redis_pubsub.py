import json
import logging
from typing import Dict, Any, Optional
import redis.asyncio as aioredis
from config import settings

logger = logging.getLogger("ShieldX.RedisPubSub")
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

class RedisPubSubService:
    @staticmethod
    def get_channel_name(parent_id: str) -> str:
        return f"channel:parent:{parent_id}"

    @staticmethod
    async def track_heartbeat(parent_id: str, fcm_token: Optional[str] = None) -> None:
        key = f"user:{parent_id}:presence"
        mapping = {"last_seen_ts": str(aioredis.Timestamp.now() / 1000.0), "is_online": "true"}
        if fcm_token: mapping["fcm_token"] = fcm_token
        async with redis_client.pipeline(transaction=True) as pipe:
            await pipe.hset(key, mapping=mapping)
            await pipe.expire(key, 45)
            await pipe.execute()

    @staticmethod
    async def get_parent_reachability(parent_id: str) -> Dict[str, Any]:
        key = f"user:{parent_id}:presence"
        data = await redis_client.hgetall(key)
        if not data or data.get("is_online") == "false":
            return {"is_online": False, "fcm_token": None}
        return {"is_online": True, "fcm_token": data.get("fcm_token")}

    @staticmethod
    async def publish_to_parent(parent_id: str, payload: Dict[str, Any]) -> bool:
        channel = RedisPubSubService.get_channel_name(parent_id)
        active_channels = await redis_client.pubsub_numsub(channel)
        listener_count = active_channels[0][1] if active_channels else 0
        if listener_count > 0:
            await redis_client.publish(channel, json.dumps(payload, default=str))
            return True
        return False