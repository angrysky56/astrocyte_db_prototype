"""Health check endpoints for monitoring system status."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_session
from ...producers import create_redis_client

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint.

    Returns:
        System health status
    """
    return {
        "status": "healthy",
        "service": "astrocyte-db",
        "version": "0.2.0",
    }


@router.get("/redis")
async def redis_health():
    """Check Redis connection health.

    Returns:
        Redis connection status
    """
    try:
        redis_client = create_redis_client()
        redis_client.ping()
        return {
            "status": "healthy",
            "service": "redis",
            "message": "Redis connection successful",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "redis",
            "error": str(e),
        }


@router.get("/database")
async def database_health(db: AsyncSession = Depends(get_db_session)):
    """Check PostgreSQL connection health.

    Args:
        db: Database session (injected)

    Returns:
        PostgreSQL connection status
    """
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "postgresql",
            "message": "Database connection successful",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "postgresql",
            "error": str(e),
        }


@router.get("/full")
async def full_health_check(db: AsyncSession = Depends(get_db_session)):
    """Complete health check of all system components.

    Args:
        db: Database session (injected)

    Returns:
        Comprehensive system health status
    """
    redis_status = await redis_health()
    db_status = await database_health(db)

    overall_healthy = (
        redis_status["status"] == "healthy" and db_status["status"] == "healthy"
    )

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "components": {
            "redis": redis_status,
            "postgresql": db_status,
        },
    }
