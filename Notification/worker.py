import asyncio
from worker_setup import notification_queue
from rq.worker import SimpleWorker
from db import init_db

async def startup():
    await init_db()

if __name__ == "__main__":
    # Initialize MongoDB before starting the worker
  

    worker = SimpleWorker(
        [notification_queue],
        connection=notification_queue.connection,
    )

    worker.work()