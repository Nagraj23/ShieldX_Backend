import logging
from redis import Redis
from rq import Queue
from config import settings

logger = logging.getLogger("ShieldX.WorkerSetup")
redis_conn = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD or None, decode_responses=False)
alert_queue = Queue("shieldx-alerts", connection=redis_conn)

def enqueue_delivery_task(notification_id: str) -> bool:
    try:
        alert_queue.enqueue("services.delivery.execute_delivery", args=(notification_id,), job_id=f"alert_{notification_id}")
        return True
    except Exception as e:
        logger.error(f"Queue error: {e}")
        return False