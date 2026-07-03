from models.sos_history import SOSHistory
from database import sos_history_collection
from utils.notifier import send_notification, play_alert_sound, is_valid_email, is_valid_phone
from datetime import datetime
from fastapi import BackgroundTasks
import asyncio
from models.sos import SOSStatus, SOSReason
from typing import Optional
from utils.network import is_online

async def save_sos_history(user_id: str, lat: float, lon: float, contacts: list, status: str = "triggered", reason: Optional[str] = None): # Modified signature
    """
    Save SOS alert to database with user ID
    """
    try:
        sos_doc = {
            "user_id": user_id,
            "location_latitude": lat,
            "location_longitude": lon,
            "timestamp": datetime.utcnow(),
            "notifiedContacts": contacts,
            "status": status,
            "reason": reason # Add reason to the document
        }

        result = await sos_history_collection.insert_one(sos_doc)
        print(f"[Database] SOS history saved with ID: {result.inserted_id} for user: {user_id}")
        return str(result.inserted_id)

    except Exception as e:
        print(f"[Database Error] Failed to save SOS history: {str(e)}")
        return None
async def trigger_sos(user_id: str, lat: float, lon: float, contacts: list, background_tasks: BackgroundTasks):
    print(f"🚨 SOS Triggered at ({lat}, {lon}) for contacts: {contacts}")

    await play_alert_sound()

    location_link = f"https://www.google.com/maps?q={lat},{lon}"
    sos_message = f"🚨 EMERGENCY: {user_id} needs help! Location: {location_link}"

    network_status = await is_online()
    notification_tasks = []

    for contact in contacts:
        if is_valid_phone(contact):
            task = send_notification(contact, sos_message, network_status)
            notification_tasks.append(task)
        elif is_valid_email(contact):
            pass # Email sending placeholder

    if notification_tasks:
        await asyncio.gather(*notification_tasks)

    # 4️⃣ Save to Database (can be done in background)
    background_tasks.add_task(
        save_sos_history,
        user_id=user_id,
        lat=lat,
        lon=lon,
        contacts=contacts,
        status="triggered",
        reason=SOSReason.MANUAL_SOS.value # Pass the reason here
    )

    print("✅ SOS process completed successfully.")

    return {
        "message": "SOS triggered successfully!",
        "contacts_notified": contacts,
        "notification_mode": "Online Mode" if network_status else "Offline Mode"
    }
