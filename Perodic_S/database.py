import logging
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ShieldX")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
sos_history_collection = db["sos_history"]
route_collection = db["route"] # This collection was already defined by the user
location_collection = db["locations"]
user_collection = db["users"]  # This is the Mongoose-managed user collection
user_routes_collection = db["user_routes"] # <-- NEW: User Route Collection

# JSON Schema validation rules for collections
# (JSON schema definitions would go here if you use them for validation at the DB level)


# Create indexes for faster queries
async def setup_indexes():
    # Create index on user_id for SOS history
    await sos_history_collection.create_index([("user_id", ASCENDING)])

    # Create index on timestamp for SOS history (for sorting by recency)
    await sos_history_collection.create_index([("timestamp", ASCENDING)])

    # Create compound index for user location history
    await location_collection.create_index([
        ("user_id", ASCENDING),
        ("timestamp", ASCENDING)
    ])

    # NEW: Indexes for user_routes collection
    await user_routes_collection.create_index([("user_id", ASCENDING)])
    await user_routes_collection.create_index([("journey_id", ASCENDING)], unique=True) # Assuming journey_id is unique per route
    await user_routes_collection.create_index([("status", ASCENDING)])
    await user_routes_collection.create_index([("last_updated_at", ASCENDING)])

    # Mongoose uses '_id' as the primary key. If you have a separate 'user_id' field,
    # make sure it's indexed. Mongoose also typically creates an index on 'email' for unique.
    # Assuming Mongoose handles 'email' unique index. If your Python code also refers to a
    # generic 'user_id' string, you might add this if not managed by Mongoose:
    # await user_collection.create_index([("user_id", ASCENDING)], unique=True)
    # The Mongoose schema uses 'email' as unique identifier, so we might need to query by email instead of 'user_id' string.
    await user_collection.create_index([("email", ASCENDING)], unique=True)  # Ensure index on email for quick lookup

    logger.info("Database indexes created successfully")

# --- Device Token Operations (Modified for Mongoose Schema) ---

async def save_device_token(user_identifier: str, token: str, token_type: str = "expo"):
    """
    Saves or updates a device token for a user within their user document.
    Since Mongoose uses 'email' as the unique identifier, we'll use that for lookup.
    """
    try:
        current_time = datetime.datetime.utcnow()

        update_result = await user_collection.update_one(
            {"email": user_identifier},  # Query by email for the user document
            {
                "$set": {
                    "deviceToken.token": token,
                    "deviceToken.type": token_type,
                    "deviceToken.updated_at": current_time
                },
                "$setOnInsert": {
                    "deviceToken.registered_at": current_time,
                }
            },
            upsert=False
        )

        if update_result.modified_count > 0:
            logger.info(f"Updated device token for user {user_identifier}: {token}")
        elif update_result.matched_count == 0:
            logger.warning(f"User with email {user_identifier} not found. Token not saved.")
        else:
            logger.info(f"Device token for user {user_identifier} already up-to-date or no changes.")

    except Exception as e:
        logger.error(f"Error saving device token for {user_identifier}: {e}")
        raise

async def get_device_token(user_identifier: str) -> str | None:
    """
    Retrieves a device token for a user from their user document.
    Uses 'email' as the lookup key.
    """
    try:
        user_doc = await user_collection.find_one({"email": user_identifier})  # Query by email
        if user_doc and "deviceToken" in user_doc and "token" in user_doc["deviceToken"]:
            logger.info(f"Retrieved token for user {user_identifier}.")
            return user_doc["deviceToken"]["token"]
        else:
            logger.info(f"No device token found for user {user_identifier}.")
            return None
    except Exception as e:
        logger.error(f"Error retrieving device token for {user_identifier}: {e}")
        raise

# Optional: Function to close the client explicitly if needed
def close_mongo_client():
    if client:
        client.close()
        logger.info("MongoDB client closed.")