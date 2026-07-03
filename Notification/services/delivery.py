import logging
import json
from datetime import datetime, timezone
from rq.exceptions import Retry
from config import settings
from db import get_alert_for_delivery, update_notification_status, get_parents_by_child
from services.redis_pubsub import RedisPubSubService
from fcm import FallbackNotificationService
from models.notification_model import Parent, DeliveryAttempt

logger = logging.getLogger("ShieldX.Worker")

async def execute_delivery(notification_id: str):
    raw_doc = await get_alert_for_delivery(notification_id)
    if not raw_doc: return {"status": "NOT_FOUND"}

    child_id = raw_doc.get("child_id")
    payload_snapshot = raw_doc.get("payload_snapshot", {})
    message = payload_snapshot.get("message", "ShieldX Safety Alert")
    recipient_ids = raw_doc.get("recipient_parent_ids", [])
    
    history = raw_doc.get("status_history", []) or []
    current_attempt_number = len(history) + 1

    parents_raw = await get_parents_by_child(child_id)
    parents = {str(p.get("_id")): Parent.model_validate(p) for p in parents_raw if p.get("_id")}

    for rec_id in recipient_ids:
        parent = parents.get(rec_id)
        if not parent: continue

        # Tier 1: Try Primary Redis Pub/Sub Memory Broker Path
        delivered = await RedisPubSubService.publish_to_parent(rec_id, payload_snapshot)
        if delivered:
            attempt = DeliveryAttempt(channel="REDIS_PUBSUB", result="SUCCESS", attempt_number=current_attempt_number)
            await update_notification_status(notification_id, {"delivered": True, "delivered_by": "REDIS_PUBSUB", "final_status": "COMPLETED"}, attempt.model_dump())
            return {"status": "SUCCESS", "channel": "REDIS_PUBSUB"}

        # Tier 2: Fallback to FCM Data Push Notification
        reach = await RedisPubSubService.get_parent_reachability(rec_id)
        if reach.get("fcm_token"):
            fcm_res = await FallbackNotificationService.dispatch_fcm_push(reach["fcm_token"], "ShieldX Emergency", message, payload_snapshot)
            if fcm_res["success"]:
                attempt = DeliveryAttempt(channel="FCM_PUSH", result="SUCCESS", attempt_number=current_attempt_number, provider_response=fcm_res)
                await update_notification_status(notification_id, {"delivered": True, "delivered_by": "FCM_PUSH", "final_status": "COMPLETED"}, attempt.model_dump())
                return {"status": "SUCCESS", "channel": "FCM_PUSH"}

        # Tier 3: Fallback to Cellular Network Twilio SMS
        if parent.phone:
            sms_res = await FallbackNotificationService.dispatch_twilio_sms(parent.phone, message)
            if sms_res["success"]:
                attempt = DeliveryAttempt(channel="TWILIO_SMS", result="SUCCESS", attempt_number=current_attempt_number, provider_response=sms_res)
                await update_notification_status(notification_id, {"delivered": True, "delivered_by": "TWILIO_SMS", "final_status": "COMPLETED"}, attempt.model_dump())
                return {"status": "SUCCESS", "channel": "TWILIO_SMS"}

    # Handle retry allocations on network drop exceptions
    if current_attempt_number < settings.MAX_DELIVERY_ATTEMPTS:
        delay = settings.INITIAL_RETRY_DELAY_SECONDS * (2 ** (current_attempt_number - 1))
        raise Retry(delay=delay)
    
    await update_notification_status(notification_id, {"delivered": False, "final_status": "FAILED"})
    return {"status": "FAILED"}