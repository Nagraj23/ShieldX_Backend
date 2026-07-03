# app/controllers/route_monitor_controller.py

from fastapi import BackgroundTasks
from pydantic import BaseModel
# Ensure this is the correct import for route sharing
from utils.route_tracker import initialize_user_tracking

class RouteShareRequest(BaseModel):
    user_id: str
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    emergency_contacts: list[str]

async def start_route_tracking(request: RouteShareRequest, background_tasks: BackgroundTasks):
    """
    Initializes tracking for a user with their planned route (source to destination).
    This function is now async because initialize_user_tracking is async.
    """
    await initialize_user_tracking(
        request.user_id,
        request.start_lat,
        request.start_lng,
        request.end_lat,
        request.end_lng,
        request.emergency_contacts
    )
    return {"status": f"Tracking initialized for {request.user_id} from ({request.start_lat}, {request.start_lng}) to ({request.end_lat}, {request.end_lng})"}