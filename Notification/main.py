import logging
import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routes.alert_routes import router as alert_router, ws_router
from services.notification_channel_listener import listen_notification_stream


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize database
    await init_db()

    # Start Redis Pub/Sub listener
    listener_task = asyncio.create_task(
        listen_notification_stream()
    )

    logging.info(
        "ShieldX Unified Notification Service Engine fully initialized."
    )

    yield

    # Shutdown Redis listener cleanly
    listener_task.cancel()

    try:
        await listener_task
    except asyncio.CancelledError:
        logging.info(
            "Notification listener task cancelled."
        )

    logging.info(
        "Shutting down Notification Core Services..."
    )


app = FastAPI(
    title="ShieldX Notification Module",
    version="2.0.0",
    lifespan=lifespan
)


# Enable CORS for mobile devices and emulators
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTP Notification APIs
app.include_router(alert_router)

# WebSocket route
app.include_router(ws_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }