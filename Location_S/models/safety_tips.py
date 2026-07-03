from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SafetyTips(BaseModel):
    id: Optional[str] = Field(alias="_id")
    user_id: Optional[str]
    scenario: Optional[str]
    safetyTip: Optional[str]
    trainingMaterials: Optional[str]
    isActive: Optional[bool] = True
    createdAt: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = Field(default_factory=datetime.utcnow) 