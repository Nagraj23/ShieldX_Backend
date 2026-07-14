from pydantic import BaseModel, Field, ConfigDict, UUID4, BeforeValidator, PlainSerializer
from typing import List, Optional, Any, Dict, Literal, Annotated
from datetime import datetime, timezone
from bson import ObjectId


def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str)
]


class GeoPoint(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None


class DeviceTelemetry(BaseModel):
    latitude: float
    longitude: float
    battery_percentage: Optional[int] = Field(default=None, ge=0, le=100)

    def to_geojson_coordinates(self) -> List[float]:
        return [self.longitude, self.latitude]


class Sender(BaseModel):
    id: str
    type: Literal[
        "USER",
        "SERVICE",
        "SYSTEM",
        "ADMIN",
        "AI"
    ] = "USER"

    name: Optional[str] = None


class Recipient(BaseModel):
    id: str
    type: Literal[
        "USER",
        "GROUP",
        "DEVICE"
    ] = "USER"

    status: Literal[
        "PENDING",
        "DELIVERED",
        "FAILED"
    ] = "PENDING"


class NotificationContent(BaseModel):
    type: str
    category: str
    priority: Literal[
        "LOW",
        "NORMAL",
        "HIGH",
        "CRITICAL"
    ] = "NORMAL"

    title: str
    body: str


class NotificationRequest(BaseModel):
    sender: Sender

    recipients: List[Recipient]

    notification: NotificationContent

    payload: Dict[str, Any] = Field(default_factory=dict)

    location: Optional[GeoPoint] = None

    telemetry: Optional[DeviceTelemetry] = None

    expires_at: Optional[datetime] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Parent(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    name: Optional[str] = None

    phone: Optional[str] = None

    fcm_token: Optional[str] = None

    is_online: bool = False

    last_seen: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


class DeliveryAttempt(BaseModel):
    channel: Literal[
        "REDIS_PUBSUB",
        "FCM_PUSH",
        "TWILIO_SMS"
    ]

    result: Literal[
        "SUCCESS",
        "FAILED_TRANSIENT",
        "FAILED_PERMANENT"
    ]

    attempt_number: int

    provider_response: Optional[Dict[str, Any]] = None

    attempted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class NotificationDocument(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    notification_id: UUID4

    sender: Sender

    recipients: List[Recipient]

    notification: NotificationContent

    payload: Dict[str, Any]

    location_geo: Optional[Dict[str, Any]] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    delivered: bool = False

    delivered_via: Optional[
        Literal[
            "REDIS_PUBSUB",
            "FCM_PUSH",
            "TWILIO_SMS"
        ]
    ] = None

    final_status: Literal[
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED"
    ] = "PENDING"

    status_history: List[DeliveryAttempt] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )