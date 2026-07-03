# app/models/user_route.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid # For generating journey_id

# Define a nested model for coordinates
class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class UserRouteStatus:
    RUNNING = "running"
    COMPLETED = "completed"
    INACTIVITY_ALERT = "inactivity_alert"
    DEVIATION_ALERT = "deviation_alert" # If you want to add this specific alert type
    PAUSED = "paused"

class UserRoute(BaseModel): # <-- Changed from Document to BaseModel
    # MongoDB _id will be automatically managed by Motor/PyMongo
    user_id: str
    journey_id: str = Field(default_factory=lambda: str(uuid.uuid4())) # Auto-generate a unique ID for each journey
    start_point: Coordinates
    end_point: Coordinates
    current_loc_coordinates: Coordinates # Will be updated frequently
    last_updated_at: datetime # To track when current_loc_coordinates was last updated
    emergency_contact: str # Stored with the route for easy access during monitoring
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default=UserRouteStatus.RUNNING) # e.g., "running", "completed", "inactivity_alert"