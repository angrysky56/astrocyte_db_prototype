"""FastAPI application entry point for Astrocyte Database.

Provides REST API for querying historical events and WebSocket
streaming for real-time event monitoring.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .. import config
from ..database import close_database, init_database
from .routes import events, health, stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks.

    Args:
        app: FastAPI application instance

    Yields:
        None during application runtime
    """
    # Startup: Initialize database
    await init_database()
    yield
    # Shutdown: Close database connections
    await close_database()


# Create FastAPI application
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description="Query and stream astrocyte-inspired event processing system",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(stream.router, prefix="/stream", tags=["streaming"])


@app.get("/")
async def root():
    """Root endpoint with API information.

    Returns:
        API metadata and available endpoints
    """
    return JSONResponse(
        content={
            "name": config.API_TITLE,
            "version": config.API_VERSION,
            "description": "Astrocyte-inspired active database API",
            "architecture": {
                "hot_tier": "Redis Streams",
                "cold_tier": "PostgreSQL + TimescaleDB",
                "cep": "Leaflet Domain Processor",
            },
            "endpoints": {
                "health": "/health",
                "events": "/events",
                "stream": "/stream/ws",
                "docs": "/docs",
            },
        }
    )
