from fastapi import APIRouter
from pydantic import BaseModel
from controllers import location_monitor_controller

location_mon_router = APIRouter()

class LocationUpdateRequest(BaseModel):
    user_id: str
    journey_id: str = None
    lat: float
    lng: float

@location_mon_router.post("/update_location")
async def update_user_location(request: LocationUpdateRequest):
    result = await location_monitor_controller.update_location_and_monitor(
        request.user_id,
        request.lat,
        request.lng,
        request.journey_id
    )
    return {"status": result}

