import asyncio
from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from database import location_collection , user_collection
from datetime import datetime
from utils.notifier import send_push_notification, play_alert_sound, is_valid_phone
from utils.network import is_online

# Define LocationRequest Data Model
class LocationRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID is required")
    username: Optional[str] = Field(None, description="Username (optional)")
    lat: float = Field(..., ge=-90, le=90, description="Latitude must be between -90 and 90")
    lng: float = Field(..., ge=-180, le=180, description="Longitude must be between -180 and 180")
    emergency_contacts: List[str] = Field(..., min_items=1, description="At least one emergency contact is required")
    is_emergency: bool = Field(default=False, description="Whether this is an emergency alert")

    @property
    def lon(self):
        return self.lng

    @property
    def contacts(self):
        return self.emergency_contacts

# Enhanced Message Generator
def generate_message(username: str, lat: float, lon: float, is_emergency: bool = False) -> str:
    """
    Generates a concise notification message with live location.
    """
    location_link = f"https://www.google.com/maps?q={lat},{lon}"
    
    if is_emergency:
        # Include the Google Maps link explicitly in the message
        message = f"🚨 EMERGENCY: {username} needs help! Location: {location_link}"
    else:
        # Include the Google Maps link explicitly in the message
        message = f"📍 {username}'s location: {location_link}"
    
    return message

# Async Notification Sender with Online/Offline Support
from utils.notifier import send_notification

async def send_notifications(contacts: list[str], message: str, is_emergency: bool = False):
    """
    Sends notifications via SMS with online/offline support
    """
    # Check network status
    network_status = await is_online()
    
    # Play alert sound for emergency
    if is_emergency:
        await play_alert_sound()
    
    # Send notifications to all contacts
    sms_tasks = []
    for contact in contacts:
        if is_valid_phone(contact):
            print(f"✅ Valid contact: {contact}")
            sms_tasks.append(send_notification(contact, message, network_status))
        else:
            print(f"⚠️ Skipping invalid contact: {contact}")

    # Execute all tasks in parallel
    results = await asyncio.gather(*sms_tasks, return_exceptions=True)
    
    for contact, result in zip(contacts, results):
        if isinstance(result, Exception):
            print(f"❌ Error sending notification to {contact}: {result}")
        else:
            print(f"📩 Notification result for {contact}: {result}")

    return network_status

# Main Async Endpoint for Location Sharing
async def get_username_by_email(email: str) -> Optional[str]:
    user_doc = await user_collection.find_one({"email": email})
    if user_doc:
        return user_doc.get("username") or user_doc.get("name") or email
    return None

async def share_location(user_id: str, lat: float, lng: float, contacts: List[str] = None, is_emergency: bool = False, username: Optional[str] = None):
    """
    Save user's location to database and send notifications
    """
    try:
        # Fetch username if not provided
        if not username:
            username = await get_username_by_email(user_id) or user_id

        # 1. Save location to database
        location_data = {
            "user_id": user_id,
            "lat": lat,
            "lng": lng,
            "timestamp": datetime.utcnow()
        }
        
        await location_collection.insert_one(location_data)
        
        # 2. Send notifications if contacts are provided
        if contacts:
            print(f"Sending notifications to contacts: {contacts}")
            message = generate_message(username, lat, lng, is_emergency)
            print(f"Generated message: {message}")
            network_status = await send_notifications(contacts, message, is_emergency)
            mode = "Online Mode" if network_status else "Offline Mode"
            print(f"Notification sending mode: {mode}")
            return {
                "status": "success", 
                "message": f"Location saved and notifications sent ({mode})",
                "notification_mode": mode
            }
        
        return {"status": "success", "message": "Location saved successfully"}
        
    except Exception as e:
        # Fix: Return JSON response with error message instead of raising Exception
        print(f"Error in share_location: {e}")
        return {"status": "error", "message": f"Failed to share location: {str(e)}"}
