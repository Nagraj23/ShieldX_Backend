from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from beanie import Document, Indexed
from enum import Enum

# Enum for SOS Status
class SOSStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"

# Enum for the Reason of the SOS alert
class SOSReason(str, Enum):
    MANUAL_SOS = "Manual SOS"               # Triggered by user directly
    INACTIVITY_ALERT = "Inactivity Alert"   # Triggered by route monitor due to no movement
    # GEOFENCE_BREACH = "Geofence Breach"     # Triggered if user leaves a defined safe zone
    ROUTE_MONITOR_ALERT = "Route Monitor Alert" # General alert from route monitoring
    LOCATION_ALERT = "Location Alert"       # General alert from location tracking
    # EMERGENCY_BUTTON = "Emergency Button"   # Specific for physical/software emergency button
    # CRITICAL_BATTERY = "Critical Battery"   # If triggered by low device battery

# Model for geographical location with a timestamp
class Location(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=datetime.now)

# Main SOS Document Model
class SOS(Document):
    user_id: Indexed(str)
    location: Location
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: SOSStatus = SOSStatus.ACTIVE
    notified_contacts: List[str] = []
    description: Optional[str] = None
    reason: Optional[SOSReason] = None      # Changed type to SOSReason Enum
    resolution_time: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    class Settings:
        name = "sos"
        indexes = [
            "user_id",
            "status",
            "created_at"
        ]