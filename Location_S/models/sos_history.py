from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(ObjectId(v))

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator):
        return {"type": "string"}

class SOSHistory(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    location_latitude: float
    location_longitude: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notifiedContacts: List[str]
    status: str = "triggered"  # triggered, resolved, false_alarm
    
    @field_serializer('timestamp')
    def serialize_dt(self, dt: datetime):
        return dt.isoformat()
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }