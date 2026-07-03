import logging
import os
import asyncio
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from twilio.rest import Client
import requests
import firebase_admin
from firebase_admin import credentials, messaging

# Load env vars
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Env Vars
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv("FIREBASE_ADMIN_KEY_PATH")
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")

# Firebase init
try:
    if not firebase_admin._apps:
        if FIREBASE_SERVICE_ACCOUNT_KEY_PATH and os.path.exists(FIREBASE_SERVICE_ACCOUNT_KEY_PATH):
            cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized.")
        else:
            logger.warning("⚠️ Firebase key not found. Push will not work.")
except Exception as e:
    logger.error(f"❌ Firebase init error: {e}")

# --- Push Notifs ---

async def send_expo_push_notification(token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
    try:
        message = {
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data or {}
        }
        response = requests.post("https://exp.host/--/api/v2/push/send", json=message)
        logger.info(f"[Expo Push] Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Expo push error: {e}")
        return False

async def send_push_notification(token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
    if token.startswith("ExponentPushToken"):
        return await send_expo_push_notification(token, title, body, data)
    elif firebase_admin._apps:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
            )
            messaging.send(message)
            return True
        except Exception as e:
            logger.error(f"[FCM Push] Error: {e}")
            return False
    else:
        logger.warning("No valid push service available.")
        return False

# --- SMS Service Class ---

class SMSService:
    def send_via_twilio(self, phone_number: str, message: str) -> Dict[str, Any]:
        if not all([TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            raise ValueError("Twilio not configured.")

        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        sms = client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=phone_number)
        logger.info(f"[Twilio] Sent SMS: SID={sms.sid}, Status={sms.status}")
        return {"sid": sms.sid, "status": sms.status}

    def send_via_fast2sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        if not FAST2SMS_API_KEY:
            raise ValueError("Fast2SMS API Key not configured.")

        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            'authorization': FAST2SMS_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            "route": "q",
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": phone_number
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        logger.info(f"[Fast2SMS] Response: {data}")

        if data.get("return") is True:
            return {"status": "sent_fast2sms"}
        else:
            raise Exception("Fast2SMS failed")

    def send_via_gsm(self, phone_number: str, message: str) -> Dict[str, Any]:
        logger.info(f"[GSM] Simulated SMS to {phone_number}: {message}")
        return {"status": "sent_simulated", "provider": "gsm_simulated"}

sms_service = SMSService()

# --- Helpers ---

async def play_alert_sound():
    logger.info("🔊 Simulating alert sound...")
    await asyncio.sleep(1)

def is_valid_email(contact: str) -> bool:
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', contact or ''))

def is_valid_phone(contact: str) -> bool:
    return bool(re.match(r'^\+?[0-9]{10,15}$', contact or ''))

async def is_online() -> bool:
    return True

# --- 🔥 Final Notification Logic with Proper Fallbacks ---

async def send_notification(contact: str, message: str, network_status: Optional[bool] = None) -> str:
    try:
        if "Emergency" in message or "🚨" in message:
            await play_alert_sound()

        if network_status is None:
            network_status = await is_online()

        if is_valid_email(contact):
            logger.info(f"📧 Email sent to {contact} (simulated)")
            return "✅ Email sent (simulated)"

        elif is_valid_phone(contact):
            # Try Twilio
            try:
                result = await asyncio.to_thread(sms_service.send_via_twilio, contact, message)
                logger.info(f"Twilio send result: {result}")
                if result.get("status") in ["queued", "sent", "delivered"]:
                    return f"✅ SMS sent via Twilio: {result['status']}"
                else:
                    logger.warning(f"Twilio gave bad status: {result['status']}")
            except Exception as e:
                logger.warning(f"Twilio failed: {e}")

            # Try Fast2SMS
            try:
                result = await asyncio.to_thread(sms_service.send_via_fast2sms, contact, message)
                logger.info(f"Fast2SMS send result: {result}")
                if result.get("status") == "sent_fast2sms":
                    return f"✅ SMS sent via Fast2SMS"
            except Exception as e:
                logger.warning(f"Fast2SMS failed: {e}")

            # Fallback to GSM if all failed
            try:
                result = await asyncio.to_thread(sms_service.send_via_gsm, contact, message)
                logger.info(f"GSM send result: {result}")
                return f"⚠️ Fallback: GSM used (offline/simulated)"
            except Exception as e:
                logger.error(f"GSM send failed: {e}")
                return f"❌ All methods failed: {e}"

        else:
            logger.error(f"Invalid contact format: {contact}")
            return "❌ Invalid contact format"
    except Exception as e:
        logger.error(f"Fatal error in notification: {e}")
        return f"❌ Error: {str(e)}"
