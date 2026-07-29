from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from services.safety_service import SafetyService
from middleware.auth_middleware import verify_jwt_token

router = APIRouter(prefix="/api/safety", tags=["Periodic Safety Engine"])
safety_service = SafetyService()


class StartSessionDTO(BaseModel):
    child_id: str = Field(..., description="The unique UUID string identifying the child profile")
    mode: str = Field(..., description="Operating mode: 'GENERAL' or 'JOURNEY'")
    estimated_duration_minutes: int = Field(0, description="Estimated route time in minutes (required if mode is JOURNEY)")
    safe_code_hash: str = Field(..., description="BCrypt formatted safe code string")
    duress_code_hash: str = Field(..., description="BCrypt formatted fake distress pin code string")
    parent_ids: List[str] = Field(..., description="Target parent user UUID identifiers")
    
class VerifyCodeDTO(BaseModel):
    child_id: str
    plain_code: str

class StopSessionDTO(BaseModel):
    child_id: str

# --- HTTP Route Endpoints (Protected by JWT Middleware) ---

@router.post("/start")
async def start_tracking_loop(payload: StartSessionDTO, user: dict = Depends(verify_jwt_token)):
    """
    Secured: Initializes a countdown sequence by capturing session configurations,
    saving variables to metadata keys, and executing dynamic randomized intervals within Redis.
    """
    try:
        success = await safety_service.start_safety_session(
            child_id=payload.child_id,
            mode=payload.mode,
            estimated_duration_minutes=payload.estimated_duration_minutes,
            safe_code_hash=payload.safe_code_hash,
            duress_code_hash=payload.duress_code_hash,
            parent_contacts=payload.parent_ids
        )
        if success:
            return {
                "status": "SUCCESS", 
                "message": f"Periodic check-in successfully initialized in [{payload.mode}] mode."
            }
        raise HTTPException(status_code=500, detail="Failed to initialize memory cache states.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_challenge_entry(payload: VerifyCodeDTO, user: dict = Depends(verify_jwt_token)):
    """
    Secured: Validates entered plain-text strings against the cached safe and duress hashes.
    Resets the active interval loop window or forces a high-severity alert stream immediately.
    """
    result = await safety_service.verify_user_code(
        child_id=payload.child_id,
        plain_code=payload.plain_code
    )
    
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=result.get("message"))
        
    return result

@router.get("/status/{child_id}")
async def get_safety_session_status(child_id: str, user: dict = Depends(verify_jwt_token)):
    """
    Secured: Returns the current status of an active periodic safety session.
    """
    result = await safety_service.get_session_status(child_id)

    if result.get("status") == "NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail=result.get("message")
        )

    return result

@router.post("/stop")
async def stop_tracking_loop(payload: StopSessionDTO, user: dict = Depends(verify_jwt_token)):
    """
    Secured: Stops an active periodic safety session.
    """
    result = await safety_service.stop_safety_session(
        child_id=payload.child_id
    )

    if result.get("status") == "NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail=result.get("message")
        )

    return result