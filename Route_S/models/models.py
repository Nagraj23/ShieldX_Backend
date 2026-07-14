from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from beanie import Document
import uuid


# ==============================
# 🔵 COMMON TYPES
# ==============================

class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


# ==============================
# 🔵 USER JOURNEY (CORE ENTITY)
# ==============================

class JourneyStatus(str):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class UserJourney(Document):
    """
    Main tracking entity for a user trip.
    Single source of truth for journey state.
    """

    user_id: str
    journey_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    start_location: Coordinates
    end_location: Coordinates
    current_location: Optional[Coordinates] = None

    status: str = JourneyStatus.ACTIVE

    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    last_movement_at: Optional[datetime] = None

    class Settings:
        name = "user_journeys"
        indexes = ["user_id", "journey_id", "status"]


# ==============================
# 🔵 LOCATION LOG (HISTORY / AUDIT)
# ==============================

class LocationLog(Document):
    """
    Stores every GPS update for audit, replay, SOS investigation.
    """

    user_id: str
    journey_id: str

    location: Coordinates
    accuracy: Optional[float] = None
    speed: Optional[float] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "location_logs"
        indexes = ["user_id", "journey_id", "timestamp"]


# ==============================
# 🔵 DEVICE STATE (TRUST LAYER)
# ==============================

class NetworkStatus(str):
    ONLINE = "online"
    LOW_SIGNAL = "low_signal"
    OFFLINE = "offline"


class GPSQuality(BaseModel):
    accuracy: float = 0.0
    confidence: float = 1.0
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserDeviceState(Document):
    """
    Represents live device health + signal reliability.
    Used for smart safety decisions.
    """

    user_id: str
    journey_id: Optional[str] = None

    is_online: bool = True
    network_status: str = NetworkStatus.ONLINE

    last_heartbeat_at: datetime = Field(default_factory=datetime.utcnow)

    gps_quality: GPSQuality

    battery_level: Optional[float] = None  # 0 - 100

    is_app_active: bool = True

    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "user_device_state"
        indexes = ["user_id", "journey_id", "last_heartbeat_at"]


# ==============================
# 🔵 JOURNEY EVENTS (EVENT SYSTEM)
# ==============================

class EventType(str):
    JOURNEY_STARTED = "journey_started"
    LOCATION_UPDATE = "location_update"
    INACTIVITY_DETECTED = "inactivity_detected"
    SIGNAL_LOSS = "signal_loss"
    JOURNEY_COMPLETED = "journey_completed"


class JourneyEvent(Document):
    """
    Event-driven backbone for Redis → Notification Service.
    """

    user_id: str
    journey_id: str

    event_type: str

    payload: dict = {}

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "journey_events"
        indexes = ["user_id", "journey_id", "event_type", "timestamp"]