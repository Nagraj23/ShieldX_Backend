from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from services.safety_service import SafetyService

router = APIRouter(prefix="/api/safety", tags=["Periodic Safety Engine"])
safety_service = SafetyService()

# --- Data Transfer Objects (DTO) / Validation Schemas ---

class StartSessionDTO(BaseModel):
    child_id: str = Field(..., description="The unique UUID string identifying the child profile")
    interval_minutes: int = Field(..., ge=1, description="Timer window block duration before verification prompt hits")
    safe_code_hash: str = Field(..., description="BCrypt formatted safe code string generated via Java Auth Service")
    duress_code_hash: str = Field(..., description="BCrypt formatted fake distress pin code string generated via Java Auth Service")
    parent_ids: List[str] = Field(..., description="Target parent user UUID identifiers used to route downstream emergency payloads")

class VerifyCodeDTO(BaseModel):
    child_id: str
    plain_code: str

# --- HTTP Route Endpoints ---

@router.post("/start")
async def start_tracking_loop(payload: StartSessionDTO):
    """
    Initializes a countdown sequence by capturing session configurations,
    saving variables to metadata keys, and executing an active TTL key within Redis memory.
    """
    try:
        success = await safety_service.start_safety_session(
            child_id=payload.child_id,
            interval_minutes=payload.interval_minutes,
            safe_code_hash=payload.safe_code_hash,
            duress_code_hash=payload.duress_code_hash,
            parent_contacts=payload.parent_ids
        )
        if success:
            return {"status": "SUCCESS", "message": "Backend periodic check timer successfully initialized."}
        raise HTTPException(status_code=500, detail="Failed to initialize memory cache states.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_challenge_entry(payload: VerifyCodeDTO):
    """
    Validates entered plain-text strings against the cached safe and duress hashes.
    Resets the active interval loop window or forces a high-severity alert stream immediately.
    """
    result = await safety_service.verify_user_code(
        child_id=payload.child_id,
        plain_code=payload.plain_code
    )
    
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=result.get("message"))
        
    return result