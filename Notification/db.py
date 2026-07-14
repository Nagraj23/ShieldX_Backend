import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings

logger = logging.getLogger("ShieldX.DB")

client: Optional[AsyncIOMotorClient] = None
db = None


async def init_db():
    global client, db

    if client is None:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.DB_NAME]
        await ensure_indexes()

    return db


async def ensure_indexes():
    try:
        await db.notifications.create_index(
            [("notification_id", 1)],
            unique=True
        )

        await db.notifications.create_index(
            [("created_at", -1)]
        )

        await db.notifications.create_index(
            [("notification.type", 1)]
        )

        await db.notifications.create_index(
            [("notification.category", 1)]
        )

        await db.notifications.create_index(
            [("notification.priority", 1)]
        )

        await db.notifications.create_index(
            [("sender.id", 1)]
        )

        await db.notifications.create_index(
            [("recipients.id", 1)]
        )

        await db.notifications.create_index(
            [("location_geo", "2dsphere")]
        )

        logger.info("Notification indexes created successfully.")

    except Exception as e:
        logger.error(f"Index creation failed: {e}")


async def insert_notification(document: Dict[str, Any]) -> str:
    if db is None:
        raise ConnectionError("Database not initialized.")

    document["_id"] = ObjectId()
    document["created_at"] = datetime.now(timezone.utc)
    document.setdefault("status_history", [])

    await db.notifications.insert_one(document)

    return str(document["_id"])


async def get_notification(notification_id: str) -> Optional[Dict[str, Any]]:
    if db is None:
        raise ConnectionError("Database not initialized.")

    obj_id = (
        ObjectId(notification_id)
        if ObjectId.is_valid(notification_id)
        else notification_id
    )

    return await db.notifications.find_one(
        {
            "_id": obj_id
        }
    )


async def update_notification_status(
    notification_id: str,
    update_data: Dict[str, Any],
    delivery_attempt: Optional[Dict[str, Any]] = None
) -> bool:

    if db is None:
        raise ConnectionError("Database not initialized.")

    obj_id = (
        ObjectId(notification_id)
        if ObjectId.is_valid(notification_id)
        else notification_id
    )

    update = {}

    if update_data:
        update["$set"] = update_data

    if delivery_attempt:
        update["$push"] = {
            "status_history": delivery_attempt
        }

    result = await db.notifications.update_one(
        {
            "_id": obj_id
        },
        update
    )

    return result.modified_count > 0