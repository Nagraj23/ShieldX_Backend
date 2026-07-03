import time
import threading
import platform
import os
import asyncio
from utils.notifier import send_push_notification, is_valid_email, is_valid_phone
from controllers.location import share_location
from fastapi import BackgroundTasks

# Get the absolute path to the assets folder
ASSETS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets"))
MP3_FILE = os.path.join(ASSETS_FOLDER, "alert.mp3")

async def trigger_sos(user_id: str, lat: float, lng: float, emergency_contacts: list[str]):
    """
    Trigger SOS alert with location sharing and notifications
    
    Args:
        user_id: User identifier
        lat: Latitude
        lng: Longitude
        emergency_contacts: List of emergency contacts
    """
    try:
        # Share location with emergency flag
        result = await share_location(
            user_id=user_id,
            lat=lat,
            lng=lng,
            contacts=emergency_contacts,
            is_emergency=True
        )
        
        return {
            "status": "success",
            "message": "SOS alert triggered successfully",
            "details": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to trigger SOS: {str(e)}"
        }