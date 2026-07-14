import logging

from redis import Redis
from rq import Queue

from config import settings

logger = logging.getLogger("ShieldX.Queue")

redis_connection = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=False,
)

notification_queue = Queue(
    name="shieldx-notifications",
    connection=redis_connection,
)


def enqueue_delivery_task(notification_id: str) -> bool:
    """
    Enqueue a notification delivery job.

    Returns:
        True if the job was successfully queued.
        False otherwise.
    """
    try:
        job = notification_queue.enqueue(
            "services.delivery.execute_delivery",
            notification_id,
            job_id=f"notification_{notification_id}",
            result_ttl=86400,       # Keep result for 24 hours
            failure_ttl=604800,     # Failed jobs retained for 7 days
        )

        logger.info(
            f"Queued notification {notification_id} "
            f"(job_id={job.id})"
        )

        return True

    except Exception:
        logger.exception(
            f"Failed to enqueue notification {notification_id}"
        )
        return False