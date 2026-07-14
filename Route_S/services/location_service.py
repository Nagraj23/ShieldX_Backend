from datetime import datetime

from database import location_logs_collection

from services.journey_service import (
    get_journey,
    update_journey_location,
)

from utils.geo_utils import haversine_distance


MOVEMENT_THRESHOLD = 10  # meters
INACTIVITY_THRESHOLD_MINUTES = 5


async def process_location_update(
    user_id: str,
    journey_id: str,
    latitude: float,
    longitude: float,
    accuracy: float | None = None,
):
    journey = await get_journey(journey_id)

    if not journey:
        raise Exception("Journey not found.")

    now = datetime.utcnow()

    previous_location = journey.get("current_location")

    movement_detected = False
    distance = 0.0

    if previous_location:

        distance = haversine_distance(
            previous_location["latitude"],
            previous_location["longitude"],
            latitude,
            longitude,
        )

        movement_detected = distance >= MOVEMENT_THRESHOLD

    await location_logs_collection.insert_one(
        {
            "user_id": user_id,
            "journey_id": journey_id,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "accuracy": accuracy,
            "timestamp": now,
        }
    )

    await update_journey_location(
        journey_id=journey_id,
        latitude=latitude,
        longitude=longitude,
        movement_detected=movement_detected,
    )

    inactivity_detected = False

    last_movement = journey.get("last_movement_at")

    if (not movement_detected) and last_movement:

        # Convert aware datetime -> naive
        if last_movement.tzinfo is not None:
            last_movement = last_movement.replace(tzinfo=None)

        print("\n========== LOCATION SERVICE ==========")
        print("Current Time :", now)
        print("Last Movement:", last_movement)
        print("Distance     :", distance)
        print("Moved        :", movement_detected)

        minutes = (now - last_movement).total_seconds() / 60

        print("Minutes Idle :", minutes)

        if minutes >= INACTIVITY_THRESHOLD_MINUTES:
            inactivity_detected = True
            print(">>> INACTIVITY DETECTED <<<")

        print("======================================\n")

    return {
        "status": "success",
        "movement_detected": movement_detected,
        "distance_moved": round(distance, 2),
        "inactivity_detected": inactivity_detected,
        "timestamp": now.isoformat(),
    }