from fastapi import APIRouter, HTTPException, Depends
from models.location_model import LocationRequest
from services.location_service import process_location_update
from db import get_username_by_user_id

router = APIRouter()


@router.post("/share-location")
async def share_location(request: LocationRequest):
    """
    API endpoint for location sharing with reason.
    """

    try:
        # Fetch username (for notification message)
        username = await get_username_by_user_id(request.user_id)

        # Fallback if username not found
        if not username:
            username = request.user_id

        # Process location update
        result = await process_location_update(
            request=request,
            username=username
        )

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
