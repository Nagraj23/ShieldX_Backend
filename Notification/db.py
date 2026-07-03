import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
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
        await db.notifications.create_index([("location_geo", "2dsphere")])
        await db.notifications.create_index([("child_id", 1)])
        logger.info("MongoDB Geospatial indexes verified successfully.")
    except Exception as e:
        logger.error(f"Failed setting database indexes: {e}")

async def get_parents_by_child(child_id: str) -> List[Dict[str, Any]]:
    if db is None: raise ConnectionError("DB offline.")
    try:
        child_doc = await db.users.find_one({"_id": child_id, "role": "CHILD"})
        if not child_doc and ObjectId.is_valid(child_id):
            child_doc = await db.users.find_one({"_id": ObjectId(child_id), "role": "CHILD"})
        if not child_doc: return []
        
        parent_ids = child_doc.get("connectedParents", [])
        query_ids = [ObjectId(pid) if ObjectId.is_valid(pid) else pid for pid in parent_ids]
        
        cursor = db.users.find({"_id": {"$in": query_ids}, "role": "PARENT"})
        return [p async for p in cursor]
    except Exception as e:
        logger.error(f"Error fetching parent profiles: {e}")
        return []

async def insert_initial_alert(wal_document: Dict[str, Any]) -> str:
    if db is None: raise ConnectionError("DB offline.")
    new_id = ObjectId()
    wal_document["_id"] = new_id
    wal_document["created_at"] = datetime.now(timezone.utc)
    wal_document["status_history"] = []
    await db.notifications.insert_one(wal_document)
    return str(new_id)

async def get_alert_for_delivery(notification_id: str) -> Optional[Dict[str, Any]]:
    if db is None: raise ConnectionError("DB offline.")
    q_id = ObjectId(notification_id) if ObjectId.is_valid(notification_id) else notification_id
    return await db.notifications.find_one({"_id": q_id})

async def update_notification_status(notification_id: str, update_data: Dict[str, Any], delivery_attempt: Optional[Dict[str, Any]] = None) -> bool:
    if db is None: raise ConnectionError("DB offline.")
    q_id = ObjectId(notification_id) if ObjectId.is_valid(notification_id) else notification_id
    mongo_update = {}
    if update_data: mongo_update["$set"] = update_data
    if delivery_attempt: mongo_update["$push"] = {"status_history": delivery_attempt}
    result = await db.notifications.update_one({"_id": q_id}, mongo_update)
    return result.modified_count > 0