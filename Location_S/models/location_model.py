from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# ---- Allowed Reasons (STRICT) ----
LocationReason = Literal[
    "SOS",
    "LOCATION_SHARE",
    "JOURNEY_START",
    "JOURNEY_UPDATE",
    "JOURNEY_END"
]

class LocationRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")

    # 🔥 MOST IMPORTANT FIELD
    reason: LocationReason = Field(..., description="Reason for location update")

    # Optional context
    journey_id: Optional[str] = Field(None, description="Journey ID if tracking")
    sos_id: Optional[str] = Field(None, description="SOS ID if emergency")

class LocationDocument(BaseModel):
    user_id: str
    lat: float
    lng: float
    reason: LocationReason

    journey_id: Optional[str] = None
    sos_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
