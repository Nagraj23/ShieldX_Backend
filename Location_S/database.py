import logging
import datetime
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING

# --------------------------------------------------
# Setup
# --------------------------------------------------

load_dotenv()
logger = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ShieldX")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# --------------------------------------------------
# Collections
# --------------------------------------------------

# SOS history
sos_history_collection = db["sos_history"]

# All location updates (SOS, share, journey)
location_collection = db["locations"]

# Journey / route tracking
user_routes_collection = db["user_routes"]

# Users (managed by Mongoose in main backend)
user_collection = db["users"]

# --------------------------------------------------
# Index Setup
# --------------------------------------------------

async def setup_indexes():
    """
    Create indexes for performance & scalability
    """

    # SOS history
    await sos_history_collection.create_index([("user_id", ASCENDING)])
    await sos_history_collection.create_index([("timestamp", ASCENDING)])

    # Location history
    await location_collection.create_index([
        ("user_id", ASCENDING),
        ("timestamp", ASCENDING)
    ])
    await location_collection.create_index([("reason", ASCENDING)])

    # Journey routes
    await user_routes_collection.create_index([("user_id", ASCENDING)])
    await user_routes_collection.create_index(
        [("journey_id", ASCENDING)], unique=True
    )
    await user_routes_collection.create_index([("status", ASCENDING)])
    await user_routes_collection.create_index([("last_updated_at", ASCENDING)])

    # Users (email is primary key in mongoose)
    await user_collection.create_index(
        [("email", ASCENDING)], unique=True
    )

    logger.info("✅ MongoDB indexes created successfully")

# --------------------------------------------------
# User Helpers
# --------------------------------------------------

async def get_username_by_user_id(user_id: str) -> str | None:
    """
    Fetch username/name using user identifier (email).
    Used for notification messages.
    """
    try:
        user = await user_collection.find_one(
            {"email": user_id},
            {"username": 1, "name": 1, "email": 1}
        )

        if not user:
            return None

        return (
            user.get("username")
            or user.get("name")
            or user.get("email")
        )

    except Exception as e:
        logger.error(f"❌ Error fetching username for {user_id}: {e}")
        return None

# --------------------------------------------------
# Device Token (Push Notification Support)
# --------------------------------------------------

async def save_device_token(
    user_identifier: str,
    token: str,
    token_type: str = "expo"
):
    """
    Save or update device token inside user document.
    Push is PRIMARY channel.
    """
    try:
        now = datetime.datetime.utcnow()

        result = await user_collection.update_one(
            {"email": user_identifier},
            {
                "$set": {
                    "deviceToken.token": token,
                    "deviceToken.type": token_type,
                    "deviceToken.updated_at": now
                },
                "$setOnInsert": {
                    "deviceToken.registered_at": now
                }
            },
            upsert=False
        )

        if result.matched_count == 0:
            logger.warning(
                f"⚠️ User not found, token not saved: {user_identifier}"
            )
        else:
            logger.info(
                f"✅ Device token saved for {user_identifier}"
            )

    except Exception as e:
        logger.error(f"❌ Error saving device token: {e}")
        raise

async def get_device_token(user_identifier: str) -> str | None:
    """
    Retrieve device token for PUSH notifications.
    """
    try:
        user = await user_collection.find_one(
            {"email": user_identifier},
            {"deviceToken.token": 1}
        )

        if user and user.get("deviceToken"):
            return user["deviceToken"].get("token")

        return None

    except Exception as e:
        logger.error(f"❌ Error fetching device token: {e}")
        return None

# --------------------------------------------------
# Close Client (Optional)
# --------------------------------------------------

def close_mongo_client():
    if client:
        client.close()
        logger.info("🛑 MongoDB client closed")
