from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from utils.route_tracker import initialize_user_tracking

share_router = APIRouter()

class RouteShareRequest(BaseModel):
    user_id: str
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    emergency_contacts: list[str]

@share_router.post("/share_route")
async def start_route_tracking(request: RouteShareRequest, background_tasks: BackgroundTasks):
    try:
        journey_id = await initialize_user_tracking(
            user_id=request.user_id,
            start_lat=request.start_lat,
            start_lng=request.start_lng,
            end_lat=request.end_lat,
            end_lng=request.end_lng,
            emergency_contacts=request.emergency_contacts  # 🔥 fixed var name
        )

        return {
            "status": "success",
            "message": "Route tracking initialized successfully!",
            "user_id": request.user_id,
            "journey_id": journey_id,  # 👈 returned from Mongo
            "start_point": {"latitude": request.start_lat, "longitude": request.start_lng},
            "end_point": {"latitude": request.end_lat, "longitude": request.end_lng},
            "emergency_contacts": request.emergency_contacts
        }

    except Exception as e:
        print(f"Error initializing route tracking for user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize route tracking: {e}")
