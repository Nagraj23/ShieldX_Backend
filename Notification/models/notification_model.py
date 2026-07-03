from pydantic import BaseModel, Field, ConfigDict, UUID4, BeforeValidator, PlainSerializer
from typing import List, Optional, Any, Dict, Literal, Annotated
from datetime import datetime, timezone
from bson import ObjectId

# =====================================================================
# STABLE PYDANTIC V2 MONGO OBJECTID TYPE DEFINITION
# =====================================================================
def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")

# Creates a type that parses inputs cleanly and serializes seamlessly into string formats
PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str)
]


# =====================================================================
# REST OF YOUR SCHEMAS (Updated to use the stable PyObjectId)
# =====================================================================
class DeviceTelemetry(BaseModel):
    latitude: float = Field(..., description="Decimal latitude coordinate.")
    longitude: float = Field(..., description="Decimal longitude coordinate.")
    battery_percentage: int = Field(..., ge=0, le=100)

    def to_geojson_coordinates(self) -> List[float]:
        return [self.longitude, self.latitude]

class GeoPoint(BaseModel):
    name: Optional[str] = None
    latitude: float = Field(...)
    longitude: float = Field(...)

class JourneyLifecycleNotification(BaseModel):
    child_id: UUID4
    event_type: Literal["JOURNEY_STARTED", "JOURNEY_COMPLETED"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    start_point: GeoPoint
    destination_point: GeoPoint
    last_recorded_location: GeoPoint
    current_telemetry: DeviceTelemetry
    estimated_duration_minutes: int
    meta_payload: Optional[Dict[str, Any]] = None

class StationaryAnomalyNotification(BaseModel):
    child_id: UUID4
    event_type: Literal["STATIONARY_DURATION_ALERT"] = "STATIONARY_DURATION_ALERT"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_spent_stationary_minutes: int = Field(..., ge=5)
    current_telemetry: DeviceTelemetry
    meta_payload: Optional[Dict[str, Any]] = None

class CriticalAlertNotification(BaseModel):
    child_id: UUID4
    alert_type: Literal["MANUAL_PANIC_SOS", "CRITICAL_LOW_BATTERY", "GEOFENCE_BREACH"]
    priority: Literal["HIGH", "CRITICAL"] = "CRITICAL"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str
    incident_trigger_location: GeoPoint
    current_telemetry: DeviceTelemetry
    meta_payload: Optional[Dict[str, Any]] = None

class Parent(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: Optional[str] = None
    phone: Optional[str] = None
    fcm_token: Optional[str] = None
    is_online: Optional[bool] = False
    last_seen: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

class DeliveryAttempt(BaseModel):
    channel: Literal["REDIS_PUBSUB", "FCM_PUSH", "TWILIO_SMS"]
    attempt_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: Literal["SUCCESS", "FAILED_TRANSIENT", "FAILED_PERMANENT"]
    provider_response: Optional[Dict[str, Any]] = None
    attempt_number: int

class UniversalNotificationLog(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    child_id: str
    category: Literal["LIFECYCLE", "ANOMALY", "CRITICAL_SOS"]
    event_type_or_alert: str
    recipient_parent_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    location_geo: Dict[str, Any]
    payload_snapshot: Dict[str, Any]
    delivered: bool = False
    delivered_via: Optional[Literal["REDIS_PUBSUB", "FCM_PUSH", "TWILIO_SMS"]] = None
    final_status: Literal["PENDING", "COMPLETED", "FAILED"] = "PENDING"

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed