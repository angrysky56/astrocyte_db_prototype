"""Database connection and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from . import config

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    config.POSTGRES_URL,
    echo=config.SQL_ECHO,
    pool_pre_ping=True,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to inject database sessions.

    Yields:
        AsyncSession: Database session with automatic cleanup

    Example:
        ```python
        @app.get("/events")
        async def get_events(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(MonoEvent))
            return result.scalars().all()
        ```
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize database tables.

    Creates all tables defined in models if they don't exist.
    Should be called on application startup.
    """
    from .models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Close database connections.

    Should be called on application shutdown to cleanly close all connections.
    """
    await engine.dispose()
