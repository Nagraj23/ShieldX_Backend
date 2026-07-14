from datetime import datetime, timezone

from database import device_state_collection


async def update_device_state(
    user_id: str,
    journey_id: str,
    gps_accuracy: float | None = None,
    battery_level: int | None = None,
    network_status: str = "online",
):
    """
    Updates the user's current device state.
    Called on every location update.
    """

    now = datetime.now(timezone.utc)

    update_fields = {
        "journey_id": journey_id,
        "network_status": network_status,
        "is_online": network_status != "offline",
        "last_heartbeat_at": now,
        "last_updated_at": now,
    }

    if gps_accuracy is not None:
        update_fields["gps_quality.accuracy"] = gps_accuracy

    if battery_level is not None:
        update_fields["battery_level"] = battery_level

    await device_state_collection.update_one(
        {
            "user_id": user_id
        },
        {
            "$set": update_fields
        },
        upsert=True,
    )


async def mark_device_offline(user_id: str):
    """
    Marks the user's device as offline.
    Used by monitoring if heartbeats stop.
    """

    now = datetime.now(timezone.utc)

    await device_state_collection.update_one(
        {
            "user_id": user_id
        },
        {
            "$set": {
                "network_status": "offline",
                "is_online": False,
                "last_updated_at": now,
            }
        }
    )


async def get_device_state(user_id: str):
    """
    Returns the latest device state.
    """

    return await device_state_collection.find_one(
        {
            "user_id": user_id
        }
    )