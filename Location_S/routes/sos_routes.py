from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from controllers.sos_controller import trigger_sos
import asyncio

sos_router = APIRouter()

class LocationRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID is required")
    lat: float = Field(..., ge=-90, le=90, description="Latitude must be between -90 and 90")
    lon: float = Field(..., ge=-180, le=180, description="Longitude must be between -180 and 180")
    contacts: list[str] = Field(..., min_items=1, description="At least one contact is required")


@sos_router.post("/sos")
async def sos_alert(request: LocationRequest, background_tasks: BackgroundTasks):
    try:
        if not request.user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Validate contacts
        if not request.contacts or len(request.contacts) == 0:
            raise HTTPException(status_code=400, detail="At least one contact is required")
        
        # Call the controller function which handles everything
        result = await trigger_sos(
            user_id=request.user_id,
            lat=request.lat,
            lon=request.lon,
            contacts=request.contacts,
            background_tasks=background_tasks
        )
        
        return {
            "status": "success",
            "message": "SOS triggered successfully!",
            "contacts_notified": request.contacts,
            "notification_mode": result.get("notification_mode", "Unknown")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))