from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.route_tracker import update_user_current_location

location_mon_router = APIRouter()

class LocationUpdateRequest(BaseModel):
    user_id: str
    lat: float
    lng: float
    journey_id: str | None = None  # Optional

@location_mon_router.post("/update_location")
async def update_location_route(payload: LocationUpdateRequest):
    """
    Updates user location and performs optional journey-based monitoring.
    """
    try:
        await update_user_current_location(
            payload.user_id, payload.lat, payload.lng, payload.journey_id
        )
        return {"status": "Location updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update location: {e}")
