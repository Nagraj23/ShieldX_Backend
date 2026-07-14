from fastapi import APIRouter, HTTPException, status

from models.notification_model import NotificationRequest
from db import insert_notification
from worker_setup import enqueue_delivery_task

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"]
)


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