from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import asyncio
import uuid
from geopy.distance import geodesic

# Project utilities
from utils.notifier import send_notification, is_valid_email, is_valid_phone
from utils.network import is_online
from controllers.sos_controller import trigger_sos
from models.sos import SOSReason, SOSStatus
from models.user_route import Coordinates, UserRouteStatus
from database import user_routes_collection

# Constants
INACTIVITY_DISTANCE_THRESHOLD_METERS = 20
INACTIVITY_TIME_THRESHOLD_MINUTES = 1
DESTINATION_REACHED_THRESHOLD_METERS = 50
NOTIFICATION_COOLDOWN_MINUTES = 2

# === Initialize tracking ===
async def initialize_user_tracking(
    user_id: str, start_lat: float, start_lng: float,
    end_lat: float, end_lng: float, emergency_contacts: list[str]
) -> str:
    now = datetime.utcnow()

    journey_id = str(uuid.uuid4())

    coords = lambda lat, lng: Coordinates(latitude=lat, longitude=lng).dict()

    new_route_doc = {
        "user_id": user_id,
        "journey_id": journey_id,
        "start_point": coords(start_lat, start_lng),
        "end_point": coords(end_lat, end_lng),
        "current_loc_coordinates": coords(start_lat, start_lng),
        "previous_loc_coordinates": coords(start_lat, start_lng),
        "last_updated_at": now,
        "emergency_contacts": emergency_contacts,
        "created_at": now,
        "status": UserRouteStatus.RUNNING,
        "last_notification_time": now
    }

    try:
        await user_routes_collection.insert_one(new_route_doc)
        print(f"✅ Initialized tracking for {user_id} | Journey ID: {journey_id}")

        route_summary = f"from ({start_lat}, {start_lng}) to ({end_lat}, {end_lng})"
        message = f"🧭 {user_id} started a journey {route_summary}. Status: Running."
        network_status = await is_online()

        for contact in emergency_contacts:
            if is_valid_email(contact) or is_valid_phone(contact):
                await send_notification(contact, message, network_status)
            else:
                print(f"⚠️ Invalid contact: {contact}, skipping notification.")

        return journey_id

    except Exception as e:
        print(f"❌ DB Error initializing journey for {user_id}: {e}")
        raise

# === Update current location ===
async def update_user_current_location(user_id: str, lat: float, lng: float, journey_id: Optional[str] = None):
    try:
        now = datetime.utcnow()
        new_coords = {"latitude": lat, "longitude": lng}

        filter_query = {"user_id": user_id, "status": UserRouteStatus.RUNNING}
        if journey_id:
            filter_query["journey_id"] = journey_id
            print(f"Attempting to update location for user {user_id}, journey {journey_id} to ({lat}, {lng})")
        else:
            print(f"No specific journey_id provided for user {user_id}. Searching for active route to update location to ({lat}, {lng}).")

        latest_route_doc = await user_routes_collection.find_one(filter_query, sort=[("last_updated_at", -1)])

        if latest_route_doc:
            existing_current_coords = latest_route_doc.get("current_loc_coordinates")
            if existing_current_coords:
                update_data = {
                    "previous_loc_coordinates": existing_current_coords,
                    "current_loc_coordinates": new_coords,
                    "last_updated_at": now
                }
            else:
                update_data = {
                    "previous_loc_coordinates": new_coords,
                    "current_loc_coordinates": new_coords,
                    "last_updated_at": now
                }

            filter_query["journey_id"] = latest_route_doc["journey_id"]
            print(f"Found active journey '{latest_route_doc['journey_id']}' for user {user_id} to update.")

            result = await user_routes_collection.update_one(filter_query, {"$set": update_data})

            if result.matched_count == 0:
                print(f"Warning: No matching active route found for user {user_id}.")
            else:
                print(f"Location updated successfully for user {user_id} ({result.matched_count} document(s) matched).")
        else:
            print(f"No active journey found for user {user_id} to update location. Skipping update.")

    except Exception as e:
        print(f"[Database Error] Failed to update location for user {user_id}: {e}")
        raise

# === Monitor all routes ===
async def monitor_all_routes_background_task():
    print("Starting background route monitoring task...")

    while True:
        await asyncio.sleep(30)

        try:
            active_routes_cursor = user_routes_collection.find({"status": UserRouteStatus.RUNNING})
            active_routes = await active_routes_cursor.to_list(length=None)

            for route_doc in active_routes:
                user_id = route_doc["user_id"]
                journey_id = route_doc["journey_id"]
                current_lat = route_doc["current_loc_coordinates"]["latitude"]
                current_lng = route_doc["current_loc_coordinates"]["longitude"]
                previous_lat = route_doc.get("previous_loc_coordinates", {}).get("latitude", current_lat)
                previous_lng = route_doc.get("previous_loc_coordinates", {}).get("longitude", current_lng)
                last_updated_at = route_doc["last_updated_at"]
                emergency_contact = route_doc["emergency_contact"]
                end_lat = route_doc["end_point"]["latitude"]
                end_lng = route_doc["end_point"]["longitude"]
                last_notification_time = route_doc.get("last_notification_time", datetime.min)

                time_since_last_update_s = (datetime.utcnow() - last_updated_at).total_seconds()

                # === Inactivity - No update ===
                if time_since_last_update_s > INACTIVITY_TIME_THRESHOLD_MINUTES * 60:
                    if (datetime.utcnow() - last_notification_time).total_seconds() > NOTIFICATION_COOLDOWN_MINUTES * 60:
                        print(f"🚨 Inactivity detected for {user_id} (Journey ID: {journey_id}) due to NO UPDATES. Triggering SOS.")
                        asyncio.create_task(trigger_sos(
                            user_id=user_id,
                            lat=current_lat,
                            lon=current_lng,
                            contacts=[emergency_contact] if emergency_contact else [],
                            reason=SOSReason.INACTIVITY_ALERT,
                            status=SOSStatus.ACTIVE
                        ))
                        await user_routes_collection.update_one(
                            {"_id": route_doc["_id"]},
                            {"$set": {
                                "status": UserRouteStatus.INACTIVITY_ALERT,
                                "last_notification_time": datetime.utcnow()
                            }}
                        )
                    else:
                        print(f"Info: Inactivity for {user_id} but still in notification cooldown.")

                # === Inactivity - No movement ===
                else:
                    distance_moved = geodesic((previous_lat, previous_lng), (current_lat, current_lng)).meters
                    if time_since_last_update_s > (INACTIVITY_TIME_THRESHOLD_MINUTES * 60) / 2 and distance_moved < INACTIVITY_DISTANCE_THRESHOLD_METERS:
                        if (datetime.utcnow() - last_notification_time).total_seconds() > NOTIFICATION_COOLDOWN_MINUTES * 60:
                            print(f"🚨 Inactivity detected for {user_id} (Journey ID: {journey_id}) due to LACK OF MOVEMENT. Triggering SOS.")
                            asyncio.create_task(trigger_sos(
                                user_id=user_id,
                                lat=current_lat,
                                lon=current_lng,
                                contacts=[emergency_contact] if emergency_contact else [],
                                reason=SOSReason.INACTIVITY_ALERT,
                                status=SOSStatus.ACTIVE
                            ))
                            await user_routes_collection.update_one(
                                {"_id": route_doc["_id"]},
                                {"$set": {
                                    "status": UserRouteStatus.INACTIVITY_ALERT,
                                    "last_notification_time": datetime.utcnow()
                                }}
                            )
                        else:
                            print(f"Info: Inactivity for {user_id} (no movement), but still in cooldown.")

                # === Destination reached ===
                if route_doc["status"] == UserRouteStatus.RUNNING:
                    distance_to_destination = geodesic((current_lat, current_lng), (end_lat, end_lng)).meters
                    if distance_to_destination < DESTINATION_REACHED_THRESHOLD_METERS:
                        if emergency_contact and (is_valid_email(emergency_contact) or is_valid_phone(emergency_contact)):
                            network_status = await is_online()
                            location_link = f"https://www.google.com/maps?q={end_lat},{end_lng}"
                            message = f"✅ {user_id} arrived at destination. Location: {location_link}"
                            print(f"Sending alert for {user_id} (Arrived): {message}")
                            await send_notification(emergency_contact, message, network_status)

                        await user_routes_collection.update_one(
                            {"_id": route_doc["_id"]},
                            {"$set": {"status": UserRouteStatus.COMPLETED}}
                        )
                        print(f"Journey for {user_id} (Journey ID: {journey_id}) completed. Status updated to 'completed'.")

        except Exception as e:
            print(f"❌ Error in background route monitoring task: {e}")
