from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback



from services.tracking_engine import update_location

router = APIRouter(
    prefix="/location",
    tags=["Location"]
)


class LocationUpdateRequest(BaseModel):
    user_id: str
    journey_id: str

    latitude: float
    longitude: float

    # Optional metadata
    accuracy: float | None = None
    battery_level: int | None = None
    network_status: str = "online"


@router.post("/update")
async def update_user_location(request: LocationUpdateRequest):
    try:

        result = await update_location(
            user_id=request.user_id,
            journey_id=request.journey_id,
            latitude=request.latitude,
            longitude=request.longitude,
            accuracy=request.accuracy,
            battery_level=request.battery_level,
            network_status=request.network_status,
        )

        return {
            "success": True,
            "message": "Location updated successfully.",
            "data": result,
        }

    except Exception:
     traceback.print_exc()

    raise HTTPException(
        status_code=500,
        detail="Internal Server Error"
    )