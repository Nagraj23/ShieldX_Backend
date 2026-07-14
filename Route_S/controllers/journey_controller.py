from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.tracking_engine import (
    start_journey,
    end_journey,
)

router = APIRouter(
    prefix="/journey",
    tags=["Journey"]
)


# ==========================================================
# REQUEST MODELS
# ==========================================================

class JourneyRequest(BaseModel):
    user_id: str
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float


class EndJourneyRequest(BaseModel):
    user_id: str
    journey_id: str


# ==========================================================
# START JOURNEY
# ==========================================================

@router.post("/start")
async def create_journey(request: JourneyRequest):

    try:

        result = await start_journey(
            user_id=request.user_id,
            start_lat=request.start_lat,
            start_lng=request.start_lng,
            end_lat=request.end_lat,
            end_lng=request.end_lng,
        )

        return {
            "success": True,
            "message": "Journey started successfully.",
            "data": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==========================================================
# END JOURNEY
# ==========================================================

@router.post("/end")
async def complete_journey(request: EndJourneyRequest):

    try:

        result = await end_journey(
            user_id=request.user_id,
            journey_id=request.journey_id,
        )

        return {
            "success": True,
            "message": "Journey completed successfully.",
            "data": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )