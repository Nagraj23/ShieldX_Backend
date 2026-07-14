import logging
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, GEOSPHERE

logger = logging.getLogger(__name__)

load_dotenv()

# ==============================
# 🔵 CONFIG
# ==============================

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ShieldX")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ==============================
# 🔵 COLLECTIONS (TRACKING SERVICE ONLY)
# ==============================

journeys_collection = db["user_journeys"]
location_logs_collection = db["location_logs"]
device_state_collection = db["user_device_state"]


# ==============================
# 🔵 INDEX SETUP (PRODUCTION READY)
# ==============================

async def setup_indexes():
    # ======================
    # JOURNEYS
    # ======================
    await journeys_collection.create_index([("user_id", ASCENDING)])
    await journeys_collection.create_index([("journey_id", ASCENDING)], unique=True)
    await journeys_collection.create_index([("status", ASCENDING)])
    await journeys_collection.create_index([
        ("user_id", ASCENDING),
        ("journey_id", ASCENDING)
    ])

    # ======================
    # LOCATION LOGS
    # ======================
    await location_logs_collection.create_index([("user_id", ASCENDING)])
    await location_logs_collection.create_index([("journey_id", ASCENDING)])
    await location_logs_collection.create_index([("timestamp", ASCENDING)])

    # 🔥 GEO SUPPORT (future: geofence, nearest tracking, deviation detection)
    await location_logs_collection.create_index([
        ("location", GEOSPHERE)
    ])

    # ======================
    # DEVICE STATE (TRUST LAYER)
    # ======================
    await device_state_collection.create_index([("user_id", ASCENDING)])
    await device_state_collection.create_index([("journey_id", ASCENDING)])
    await device_state_collection.create_index([("last_heartbeat_at", ASCENDING)])

    logger.info("✅ Tracking DB indexes initialized successfully")


# ==============================
# 🔵 CLEAN SHUTDOWN
# ==============================

def close_mongo_client():
    if client:
        client.close()
        logger.info("MongoDB connection closed")