from typing import Dict, Any
from models.location_model import LocationRequest, LocationDocument
from utils.reason_mapper import get_reason_config
from utils.message_builder import build_location_message
from services.notification_bridge import send_location_alert_to_notifier
from database import location_collection


async def process_location_update(
    request: LocationRequest,
    username: str
) -> Dict[str, Any]:
    """
    Core service to:
    1. Save location with reason
    2. Decide if notification is required
    3. Forward alert to notification module (if needed)
    """

    # 1️⃣ Fetch behavior based on reason
    reason_config = get_reason_config(request.reason)

    # 2️⃣ Save location to DB (ALWAYS)
    location_doc = LocationDocument(
        user_id=request.user_id,
        lat=request.lat,
        lng=request.lng,
        reason=request.reason,
        journey_id=request.journey_id,
        sos_id=request.sos_id
    )

    await location_collection.insert_one(location_doc.dict())

    # 3️⃣ If no notification needed (e.g. JOURNEY_UPDATE), stop here
    if not reason_config["notify"]:
        return {
            "status": "stored_only",
            "reason": request.reason
        }

    # 4️⃣ Build human-readable message
    message = build_location_message(
        username=username,
        lat=request.lat,
        lng=request.lng,
        reason=request.reason
    )

    # 5️⃣ Prepare payload for notification service
    payload = {
        "lat": request.lat,
        "lng": request.lng,
        "reason": request.reason,
        "journey_id": request.journey_id,
        "sos_id": request.sos_id,
        "maps_link": f"https://www.google.com/maps?q={request.lat},{request.lng}"
    }

    # 6️⃣ Send to Universal Notification Module
    notifier_response = await send_location_alert_to_notifier(
        user_id=request.user_id,
        message=message,
        reason=request.reason,
        priority=reason_config["priority"],
        payload=payload
    )

    return {
        "status": "notified",
        "reason": request.reason,
        "notification_id": notifier_response.get("notification_id")
    }
