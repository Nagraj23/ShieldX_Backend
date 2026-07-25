import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings


logger = logging.getLogger("ShieldX.DB")


client: Optional[AsyncIOMotorClient] = None
db = None


async def init_db():
    global client, db

    if client is None:
        client = AsyncIOMotorClient(
            settings.MONGO_URI
        )
        db = client[settings.DB_NAME]
        await ensure_indexes()
        logger.info(
            "MongoDB initialized"
        )

    return db


def get_notifications_collection():
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db.notifications


async def ensure_indexes():
    notification_coll = get_notifications_collection()
    
    await notification_coll.create_index(
        [("notification_id", 1)],
        unique=True
    )

    await notification_coll.create_index(
        [("created_at", -1)]
    )

    await notification_coll.create_index(
        [("recipients.id", 1)]
    )


async def get_user_notifications(
    user_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    notification_coll = get_notifications_collection()

    cursor = notification_coll.find(
        {
            "$or": [
                {"recipient_id": user_id},
                {"recipients.id": user_id}
            ]
        }
    ).sort(
        "created_at",
        -1
    ).limit(limit)

    notifications = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        notifications.append(doc)

    return notifications


async def insert_notification(
    document: Dict[str, Any]
) -> str:
    notification_coll = get_notifications_collection()

    document["_id"] = ObjectId()

    document["created_at"] = datetime.now(
        timezone.utc
    )

    document.setdefault(
        "status_history",
        []
    )

    await notification_coll.insert_one(
        document
    )

    return str(document["_id"])


async def get_notification(
    notification_id: str
):
    notification_coll = get_notifications_collection()

    obj_id = (
        ObjectId(notification_id)
        if ObjectId.is_valid(notification_id)
        else notification_id
    )

    return await notification_coll.find_one(
        {
            "_id": obj_id
        }
    )


async def update_notification_status(
    notification_id: str,
    update_data: Dict[str, Any],
    delivery_attempt=None
):
    notification_coll = get_notifications_collection()

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

    result = await notification_coll.update_one(
        {
            "_id": obj_id
        },
        update
    )

    return result.modified_count > 0