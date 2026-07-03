import redis.asyncio as aioredis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Connection pool instance for global application reuse
redis_pool = aioredis.ConnectionPool(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    db=REDIS_DB, 
    decode_responses=True
)

def get_redis_client() -> aioredis.Redis:
    """Returns a non-blocking Redis client initialized from the pool."""
    return aioredis.Redis(connection_pool=redis_pool)