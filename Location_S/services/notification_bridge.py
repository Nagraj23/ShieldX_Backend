import httpx
from typing import Dict, Any

# URL of Universal Notification Module
NOTIFICATION_SERVICE_URL = "http://localhost:8001/api/v1/alert/send"


async def send_location_alert_to_notifier(
    user_id: str,
    message: str,
    reason: str,
    priority: str,
    payload: Dict[str, Any]
):
    """
    Sends location-related alerts to the Universal Notification Module.
    Push is PRIMARY, SMS is FALLBACK (handled there).
    """

    request_body = {
        "child_id": user_id,
        "message": message,
        "alert_type": reason,
        "priority": priority,
        "payload": payload
    }

    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(
            NOTIFICATION_SERVICE_URL,
            json=request_body
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Notification service error: {response.status_code} - {response.text}"
        )

    return response.json()
