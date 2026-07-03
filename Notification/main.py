import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from db import init_db
from routes.alert_routes import router as alert_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce clear asynchronous connection setup on server boot
    await init_db()
    logging.info("ShieldX Unified Notification Service Engine fully initialized.")
    yield
    logging.info("Shutting down Notification Core Services...")

app = FastAPI(title="ShieldX Notification Module", version="2.0.0", lifespan=lifespan)
app.include_router(alert_router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}