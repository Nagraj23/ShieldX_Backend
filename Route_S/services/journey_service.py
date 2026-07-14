from datetime import datetime, timezone
import uuid

from database import journeys_collection


# ==========================================================
# CREATE JOURNEY
# ==========================================================

async def create_journey(
    user_id: str,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
):
    """
    Creates a new journey and returns its details.
    """

    now = datetime.now(timezone.utc)

    journey_id = str(uuid.uuid4())

    journey = {
        "user_id": user_id,
        "journey_id": journey_id,

        "start_location": {
            "latitude": start_lat,
            "longitude": start_lng
        },

        "end_location": {
            "latitude": end_lat,
            "longitude": end_lng
        },

        "current_location": {
            "latitude": start_lat,
            "longitude": start_lng
        },

        "status": "active",

        "started_at": now,
        "last_updated_at": now,
        "last_movement_at": now,
        "completed_at": None,
    }

    await journeys_collection.insert_one(journey)

    return {
        "journey_id": journey_id,
        "user_id": user_id,
        "status": "active"
    }


# ==========================================================
# GET JOURNEY
# ==========================================================

async def get_journey(journey_id: str):
    """
    Returns a journey document.
    """

    return await journeys_collection.find_one(
        {"journey_id": journey_id}
    )


# ==========================================================
# UPDATE CURRENT LOCATION
# ==========================================================

async def update_journey_location(
    journey_id: str,
    latitude: float,
    longitude: float,
    movement_detected: bool = False,
):
    """
    Updates the user's current location.
    """

    now = datetime.now(timezone.utc)

    update_fields = {
        "current_location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "last_updated_at": now,
    }

    if movement_detected:
        update_fields["last_movement_at"] = now

    await journeys_collection.update_one(
        {
            "journey_id": journey_id,
            "status": "active"
        },
        {
            "$set": update_fields
        }
    )


# ==========================================================
# COMPLETE JOURNEY
# ==========================================================

async def complete_journey(
    user_id: str,
    journey_id: str,
):
    """
    Marks a journey as completed.
    """

    now = datetime.now(timezone.utc)

    result = await journeys_collection.update_one(
        {
            "user_id": user_id,
            "journey_id": journey_id,
            "status": "active",
        },
        {
            "$set": {
                "status": "completed",
                "completed_at": now,
                "last_updated_at": now,
            }
        }
    )

    if result.modified_count == 0:
        raise Exception("Journey not found or already completed.")

    return {
        "journey_id": journey_id,
        "status": "completed",
        "completed_at": now.isoformat(),
    }


# ==========================================================
# UPDATE JOURNEY STATUS
# ==========================================================

async def update_journey_status(
    journey_id: str,
    status: str,
):
    """
    Generic status updater.
    """

    await journeys_collection.update_one(
        {
            "journey_id": journey_id
        },
        {
            "$set": {
                "status": status,
                "last_updated_at": datetime.now(timezone.utc)
            }
        }
    )