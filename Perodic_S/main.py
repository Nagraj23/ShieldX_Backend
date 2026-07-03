import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from controllers.safety_controller import router as safety_router
from services.redis_listener import listen_to_timer_expirations

# Configure system level application logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app_main")

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Handles background daemon scheduling and resource cleanups side-by-side 
    with the core HTTP server lifecycle hooks.
    """
    logger.info("[STARTUP] Spawning asynchronous background task engines...")
    
    # Initialize the Redis keyspace evictions monitor task without blocking HTTP bindings
    listener_task = asyncio.create_task(listen_to_timer_expirations())
    logger.info("[STARTUP] Asynchronous Redis Keyspace listener active and monitoring active slots.")
    
    yield  # Hand control back to server to accept inbound request maps
    
    logger.info("[SHUTDOWN] Terminating persistent application pipelines...")
    
    # Cleanly terminate background thread workers during application process tear-downs
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        logger.info("[SHUTDOWN] Redis Keyspace background worker cleanly dismantled.")
    logger.info("[SHUTDOWN] Application environment state reset completely.")

app = FastAPI(
    title="ShieldX Periodic Safety Microservice",
    description="High-throughput, asynchronous Redis-backed ticking engine for real-time safety monitoring.",
    version="1.0.0",
    lifespan=app_lifespan
)

# Attach routes to app instance
app.include_router(safety_router)

@app.get("/")
async def root_sanity_check():
    """
    Health check heartbeat loop mapping target flags.
    """
    return {
        "service": "ShieldX Periodic Safety Microservice",
        "status": "ONLINE",
        "engine": "FastAPI Async Loop Framework"
    }