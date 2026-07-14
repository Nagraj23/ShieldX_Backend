import asyncio
import redis.asyncio as redis

async def main():
    client = redis.Redis(
        host="127.0.0.1",
        port=6379,
        decode_responses=True
    )

    print(await client.ping())

asyncio.run(main())