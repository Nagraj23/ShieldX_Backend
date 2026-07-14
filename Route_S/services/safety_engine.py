from datetime import datetime

from utils.geo_utils import haversine_distance
from utils.redis_publisher import (
    publish_inactivity_detected,
    publish_low_signal,
    publish_location_lost,
    publish_route_deviation,
    publish_destination_reached,
    publish_low_battery,
)

INACTIVITY_MINUTES = 5
LOCATION_TIMEOUT_MINUTES = 2
LOW_BATTERY_PERCENT = 15
LOW_GPS_ACCURACY = 50
DESTINATION_RADIUS = 30
ROUTE_DEVIATION_RADIUS = 150


async def evaluate_safety(
    journey: dict,
    device_state: dict | None,
    movement_result: dict,
):

    now = datetime.utcnow()

    print("\n========== SAFETY ENGINE ==========")
    print("Current Time :", now)
    print("Journey ID   :", journey.get("journey_id"))
    print("User ID      :", journey.get("user_id"))
    print("===================================\n")

    events = []

    if movement_result.get("inactivity_detected"):

        print("[Safety] Inactivity detected")

        payload = {
            "event": "tracking.inactivity",
            "user_id": journey["user_id"],
            "journey_id": journey["journey_id"],
            "location": journey["current_location"],
            "timestamp": now.isoformat(),
        }

        await publish_inactivity_detected(payload)

        events.append("INACTIVITY")

    if device_state:

        gps_accuracy = (
            device_state.get("gps_quality", {})
            .get("accuracy")
        )

        print(f"[Safety] GPS Accuracy : {gps_accuracy}")

        if gps_accuracy is not None and gps_accuracy >= LOW_GPS_ACCURACY:

            print("[Safety] Low GPS detected")

            payload = {
                "event": "tracking.low_signal",
                "user_id": journey["user_id"],
                "journey_id": journey["journey_id"],
                "accuracy": gps_accuracy,
                "timestamp": now.isoformat(),
            }

            await publish_low_signal(payload)

            events.append("LOW_SIGNAL")

    if device_state:

        heartbeat = device_state.get("last_heartbeat_at")

        print(f"[Safety] Heartbeat : {heartbeat}")

        if heartbeat:

            print("Heartbeat tzinfo :", heartbeat.tzinfo)
            print("Now tzinfo       :", now.tzinfo)

            if heartbeat.tzinfo is not None:
                heartbeat = heartbeat.replace(tzinfo=None)

            print("Heartbeat After  :", heartbeat)
            print("Now              :", now)

            minutes = (now - heartbeat).total_seconds() / 60

            print(f"[Safety] Minutes Since Heartbeat : {minutes}")

            if minutes >= LOCATION_TIMEOUT_MINUTES:

                print("[Safety] Device Offline")

                payload = {
                    "event": "tracking.location_lost",
                    "user_id": journey["user_id"],
                    "journey_id": journey["journey_id"],
                    "timestamp": now.isoformat(),
                }

                await publish_location_lost(payload)

                events.append("LOCATION_LOST")

    if device_state:

        battery = device_state.get("battery_level")

        print(f"[Safety] Battery : {battery}")

        if battery is not None and battery <= LOW_BATTERY_PERCENT:

            print("[Safety] Low Battery")

            payload = {
                "event": "tracking.low_battery",
                "user_id": journey["user_id"],
                "journey_id": journey["journey_id"],
                "battery": battery,
                "timestamp": now.isoformat(),
            }

            await publish_low_battery(payload)

            events.append("LOW_BATTERY")

    current = journey.get("current_location")
    destination = journey.get("destination")

    if current and destination:

        distance = haversine_distance(
            current["latitude"],
            current["longitude"],
            destination["latitude"],
            destination["longitude"],
        )

        print(f"[Safety] Distance to Destination : {distance}")

        if distance <= DESTINATION_RADIUS:

            print("[Safety] Destination Reached")

            payload = {
                "event": "tracking.destination_reached",
                "user_id": journey["user_id"],
                "journey_id": journey["journey_id"],
                "timestamp": now.isoformat(),
            }

            await publish_destination_reached(payload)

            events.append("DESTINATION_REACHED")

    if movement_result.get("route_deviation"):

        print("[Safety] Route Deviation")

        payload = {
            "event": "tracking.route_deviation",
            "user_id": journey["user_id"],
            "journey_id": journey["journey_id"],
            "location": journey["current_location"],
            "timestamp": now.isoformat(),
        }

        await publish_route_deviation(payload)

        events.append("ROUTE_DEVIATION")

    print("\nTriggered Events :", events)
    print("===================================\n")

    return {
        "status": "evaluated",
        "events": events,
    }