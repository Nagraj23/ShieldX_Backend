from fastapi import APIRouter, HTTPException, status
from typing import Union
from models.notification_model import JourneyLifecycleNotification, StationaryAnomalyNotification, CriticalAlertNotification
from db import insert_initial_alert, get_parents_by_child
from worker_setup import enqueue_delivery_task

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])
AlertUnion = Union[JourneyLifecycleNotification, StationaryAnomalyNotification, CriticalAlertNotification]

@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def ingest_alert(payload: AlertUnion):
    try:
        parents = await get_parents_by_child(str(payload.child_id))
        if not parents:
            raise HTTPException(status_code=404, detail="No guardians registered for this device.")
        
        recipient_ids = [str(p["_id"]) for p in parents]
        
        coords = [0.0, 0.0]
        if hasattr(payload, 'current_telemetry'):
            coords = payload.current_telemetry.to_geojson_coordinates()
        
        wal_doc = {
            "child_id": str(payload.child_id),
            "category": "LIFECYCLE" if hasattr(payload, 'event_type') and "JOURNEY" in payload.event_type else "ANOMALY" if hasattr(payload, 'duration_spent_stationary_minutes') else "CRITICAL_SOS",
            "event_type_or_alert": getattr(payload, 'event_type', getattr(payload, 'alert_type', "SOS")),
            "recipient_parent_ids": recipient_ids,
            "location_geo": {"type": "Point", "coordinates": coords},
            "payload_snapshot": payload.model_dump()
        }
        
        notification_id = await insert_initial_alert(wal_doc)
        enqueue_delivery_task(notification_id)
        
        return {"status": "queued", "notification_id": notification_id}
    except HTTPException as he: raise he
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Queue Failure: {e}")