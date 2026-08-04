import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.safety_controller import router as safety_router
from services.safety_service import SafetyService
from config.redis_config import get_redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app_main")

async def listen_to_timer_expirations():
    redis_client = get_redis_client()
    safety_service = SafetyService()
    
    pubsub = redis_client.pubsub()
    channel = "__keyevent@0__:expired"

    await pubsub.subscribe(channel)
    logger.info("🟢 [Redis Listener] Subscribed to keyspace expiration events.")

    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage" or message["type"] == "message":
                raw_data = message["data"]
                
                # 🛡️ Safely handle data whether it arrives as bytes or string
                if isinstance(raw_data, bytes):
                    expired_key = raw_data.decode("utf-8")
                elif isinstance(raw_data, str):
                    expired_key = raw_data
                else:
                    continue
                
                # 1. Main periodic interval expired -> Trigger a check-in request
                if expired_key.startswith("periodic:timer:"):
                    child_id = expired_key.replace("periodic:timer:", "")
                    logger.info(f"⏰ Main timer expired for child {child_id}. Sending check-in.")
                    await safety_service.send_checkin_request(child_id)

                # 2. Response window expired without PIN entry -> Trigger retry or SOS
                elif expired_key.startswith("periodic:response:"):
                    child_id = expired_key.replace("periodic:response:", "")
                    logger.warning(f"⚠️ Response window lapsed for child {child_id}. Evaluating retry loop.")
                    await safety_service.handle_no_response(child_id)
                    
    except asyncio.CancelledError:
        logger.info("🛑 Redis keyspace listener task cancelled cleanly.")
    except Exception as e:
        logger.error(f"❌ Error in Redis keyspace listener: {e}")
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.info("[STARTUP] Spawning asynchronous background task engines...")
    listener_task = asyncio.create_task(listen_to_timer_expirations())
    logger.info("[STARTUP] Asynchronous Redis Keyspace listener active.")
    yield
    logger.info("[SHUTDOWN] Terminating persistent application pipelines...")
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

# 🔥 Enable CORS Middleware for Mobile Frontend Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(safety_router)

@app.get("/")
async def root_sanity_check():
    return {
        "service": "ShieldX Periodic Safety Microservice",
        "status": "ONLINE",
        "engine": "FastAPI Async Loop Framework"
    }