from services.journey_service import (
    create_journey,
    complete_journey,
    get_journey,
)

from services.location_service import (
    process_location_update,
)

from services.device_service import (
    update_device_state,
    get_device_state,
)

from services.safety_engine import (
    evaluate_safety,
)

from utils.redis_publisher import (
    publish_journey_started,
    publish_journey_completed,
)


# ==========================================================
# START JOURNEY
# ==========================================================

async def start_journey(
    user_id: str,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
):

    journey = await create_journey(
        user_id=user_id,
        start_lat=start_lat,
        start_lng=start_lng,
        end_lat=end_lat,
        end_lng=end_lng,
    )

    await publish_journey_started(journey)

    return journey


# ==========================================================
# LOCATION UPDATE
# ==========================================================

async def update_location(
    user_id: str,
    journey_id: str,
    latitude: float,
    longitude: float,
    accuracy: float | None = None,
    battery_level: int | None = None,
    network_status: str = "online",
):

    # ------------------------------------------
    # Verify Journey Exists
    # ------------------------------------------

    journey = await get_journey(journey_id)

    if journey is None:
        raise Exception("Journey not found.")

    # ------------------------------------------
    # Process Location
    # ------------------------------------------

    movement_result = await process_location_update(
        user_id=user_id,
        journey_id=journey_id,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
    )

    # ------------------------------------------
    # Update Device State
    # ------------------------------------------

    await update_device_state(
        user_id=user_id,
        journey_id=journey_id,
        gps_accuracy=accuracy,
        battery_level=battery_level,
        network_status=network_status,
    )

    # ------------------------------------------
    # Fetch Updated State
    # ------------------------------------------

    latest_journey = await get_journey(journey_id)

    device_state = await get_device_state(user_id)

    # ------------------------------------------
    # Safety Evaluation
    # ------------------------------------------

    safety_result = await evaluate_safety(
        journey=latest_journey,
        device_state=device_state,
        movement_result=movement_result,
    )

    return {
        "success": True,
        "journey_id": journey_id,
        "movement": movement_result,
        "safety": safety_result,
    }


# ==========================================================
# END JOURNEY
# ==========================================================

async def end_journey(
    user_id: str,
    journey_id: str,
):

    journey = await get_journey(journey_id)

    if journey is None:
        raise Exception("Journey not found.")

    result = await complete_journey(
        user_id=user_id,
        journey_id=journey_id,
    )

    await publish_journey_completed(result)

    return result