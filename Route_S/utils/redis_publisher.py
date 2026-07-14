import json
import os

from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

print(f"Connecting Redis -> {REDIS_HOST}:{REDIS_PORT}")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)


async def publish(channel: str, payload: dict):
    """
    Generic Redis publisher.
    """

    await redis_client.publish(
        channel,
        json.dumps(payload)
    )


# =====================================================
# Journey Events
# =====================================================

async def publish_journey_started(payload: dict):
    await publish("journey.started", payload)


async def publish_journey_completed(payload: dict):
    await publish("journey.completed", payload)


# =====================================================
# Monitoring Events
# =====================================================

async def publish_inactivity_detected(payload: dict):
    await publish("journey.inactivity", payload)


async def publish_low_signal(payload: dict):
    await publish("journey.low_signal", payload)


async def publish_location_lost(payload: dict):
    await publish("journey.location_lost", payload)
    
async def publish_route_deviation(payload: dict):
    await publish("tracking.route_deviation", payload)


async def publish_destination_reached(payload: dict):
    await publish("tracking.destination_reached", payload)


async def publish_low_battery(payload: dict):
    await publish("tracking.low_battery", payload)