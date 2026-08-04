import logging
import asyncio
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from models.notification_model import NotificationRequest
from db import insert_notification
from worker_setup import enqueue_delivery_task
from services.redis_pubsub import track_heartbeat, get_user_channel, redis_client
from db import get_user_notifications

logger = logging.getLogger("ShieldX.AlertRoutes")

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"]
)

class HeartbeatRequest(BaseModel):
    user_id: str
    fcm_token: str

@router.get("/user/{user_id}")
async def fetch_notifications(user_id: str):

    try:
        notifications = await get_user_notifications(
            user_id
        )

        return notifications

    except Exception as e:
        logger.error(
            f"Fetch notifications failed: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch notifications"
        )
        
# 📌 1. Heartbeat Route (Registers Redis Presence & FCM Token)
@router.post("/heartbeat", status_code=status.HTTP_200_OK)
async def register_heartbeat(payload: HeartbeatRequest):
    try:
        await track_heartbeat(payload.user_id, payload.fcm_token)
        return {"status": "SUCCESS", "message": "Heartbeat recorded"}
    except Exception as e:
        logger.error(f"Heartbeat tracking failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Heartbeat failure: {str(e)}"
        )


# 📌 2. Tier 1 WebSocket Route (Real-Time Push Channel)
# Mounted at: /ws/notifications/{user_id}
# Note: Root router mounts WebSocket without prefix collision
ws_router = APIRouter()

@ws_router.websocket("/ws/notifications/{user_id}")
async def notification_websocket(websocket: WebSocket, user_id: str):

    await websocket.accept()

    logger.info(
        f"⚡ [WebSocket Connected] User: {user_id}"
    )

    pubsub = None
    channel_name = get_user_channel(user_id)

    try:
        pubsub = redis_client.pubsub()

        await pubsub.subscribe(channel_name)

        while True:

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0
            )

            if message and message["type"] == "message":

                data = message["data"]

                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                await websocket.send_text(data)

            await asyncio.sleep(0.1)


    except WebSocketDisconnect:

        logger.info(
            f"🔌 [WebSocket Disconnected] User: {user_id}"
        )


    except Exception as e:

        logger.error(
            f"❌ WebSocket Error {user_id}: {e}"
        )


    finally:

        if pubsub:

            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()

                logger.info(
                    f"🧹 Redis PubSub cleaned: {user_id}"
                )

            except Exception as e:

                logger.error(
                    f"Redis cleanup failed: {e}"
                )

# 📌 3. Submit Notification Dispatch Endpoint
@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def send_notification(payload: NotificationRequest):
    try:
        wal_doc = {
            "notification_id": str(payload.notification_id),
            "sender": payload.sender.model_dump(),
            "recipients": [r.model_dump() for r in payload.recipients],
            "notification": payload.notification.model_dump(),
            "payload": payload.payload,
            "location_geo": (
                {
                    "type": "Point",
                    "coordinates": payload.telemetry.to_geojson_coordinates()
                }
                if payload.telemetry
                else None
            ),
            "created_at": payload.created_at,
            "expires_at": payload.expires_at,
            "delivered": False,
            "final_status": "PENDING",
            "status_history": []
        }

        notification_id = await insert_notification(wal_doc)
        enqueue_delivery_task(notification_id)

        return {
            "status": "QUEUED",
            "notification_id": notification_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Notification queue failure: {str(e)}"
        )
        
@router.put("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_as_read(notification_id: str):
    try:
        from db import get_notifications_collection
        notif_coll = get_notifications_collection()

        # Handle both string ID or MongoDB ObjectId fields
        query = {}
        if len(notification_id) == 24:
            try:
                query = {"$or": [{"notification_id": notification_id}, {"_id": ObjectId(notification_id)}]}
            except:
                query = {"notification_id": notification_id}
        else:
            query = {"notification_id": notification_id}

        result = await notif_coll.update_one(
            query,
            {
                "$set": {
                    "delivered": True,
                    "read": True,
                    "final_status": "COMPLETED"
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"status": "SUCCESS", "message": "Notification marked as read"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating notification: {str(e)}"
        )


# 📌 5. Clear / Delete Notification Route
@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(notification_id: str):
    try:
        from db import get_notifications_collection
        notif_coll = get_notifications_collection()

        query = {}
        if len(notification_id) == 24:
            try:
                query = {"$or": [{"notification_id": notification_id}, {"_id": ObjectId(notification_id)}]}
            except:
                query = {"notification_id": notification_id}
        else:
            query = {"notification_id": notification_id}

        result = await notif_coll.delete_one(query)

        if result.deleted_count == 0:
            return {"status": "NOT_FOUND", "message": "Notification already removed or doesn't exist"}

        return {"status": "SUCCESS", "message": "Notification deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting notification: {str(e)}"
        )