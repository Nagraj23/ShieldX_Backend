from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import setup_indexes

from controllers.journey_controller import router as journey_router
from controllers.location_controller import router as location_router


# ==========================================================
# Application Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on application startup and shutdown.
    """

    print("Starting Tracking Service...")

    # Create MongoDB indexes
    await setup_indexes()

    print("Tracking Service started successfully.")

    yield

    print("Shutting down Tracking Service...")


# ==========================================================
# FastAPI App
# ==========================================================

app = FastAPI(
    title="ShieldX Tracking Service",
    version="1.0.0",
    description="Safety Navigation & Journey Tracking Service",
    lifespan=lifespan,
)


# ==========================================================
# Register Routers
# ==========================================================

app.include_router(journey_router)
app.include_router(location_router)


# ==========================================================
# Health Check
# ==========================================================

@app.get("/")
async def root():
    return {
        "service": "Tracking Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }