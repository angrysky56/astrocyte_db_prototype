"""Event query endpoints for historical event data.

Provides REST API for querying mono-originated and multi-originated events
from the persistent storage layer (PostgreSQL).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_session
from ...models import MonoEvent, MultiEvent

router = APIRouter()


@router.get("/mono")
async def query_mono_events(
    start_time: datetime | None = Query(None, description="Start of time range"),
    end_time: datetime | None = Query(None, description="End of time range"),
    source_stream: str | None = Query(None, description="Filter by source stream"),
    event_type: str | None = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Query mono-originated events with flexible filtering.

    Args:
        start_time: Filter events after this timestamp
        end_time: Filter events before this timestamp
        source_stream: Filter by source stream (e.g., 'stream:axon_1')
        event_type: Filter by event type
        limit: Maximum number of results (1-1000)
        offset: Number of results to skip for pagination
        db: Database session (injected)

    Returns:
        Dictionary containing query metadata and event list
    """
    # Build dynamic query
    query = select(MonoEvent).order_by(MonoEvent.timestamp.desc())

    if start_time:
        query = query.where(MonoEvent.timestamp >= start_time)
    if end_time:
        query = query.where(MonoEvent.timestamp <= end_time)
    if source_stream:
        query = query.where(MonoEvent.source_stream == source_stream)
    if event_type:
        query = query.where(MonoEvent.event_type == event_type)

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "count": len(events),
        "limit": limit,
        "offset": offset,
        "events": [
            {
                "event_id": str(event.event_id),
                "timestamp": event.timestamp.isoformat(),
                "source_stream": event.source_stream,
                "event_type": event.event_type,
                "value": event.value,
                "metadata": event.metadata,
            }
            for event in events
        ],
    }


@router.get("/multi")
async def query_multi_events(
    start_time: datetime | None = Query(None, description="Start of time range"),
    end_time: datetime | None = Query(None, description="End of time range"),
    correlation_rule: str | None = Query(None, description="Filter by correlation rule"),
    min_confidence: float | None = Query(None, ge=0, le=1, description="Minimum confidence"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Query multi-originated (integrated) events with flexible filtering.

    Args:
        start_time: Filter events after this timestamp
        end_time: Filter events before this timestamp
        correlation_rule: Filter by correlation rule used
        min_confidence: Minimum confidence threshold (0.0-1.0)
        limit: Maximum number of results (1-1000)
        offset: Number of results to skip for pagination
        db: Database session (injected)

    Returns:
        Dictionary containing query metadata and event list
    """
    # Build dynamic query
    query = select(MultiEvent).order_by(MultiEvent.timestamp.desc())

    if start_time:
        query = query.where(MultiEvent.timestamp >= start_time)
    if end_time:
        query = query.where(MultiEvent.timestamp <= end_time)
    if correlation_rule:
        query = query.where(MultiEvent.correlation_rule == correlation_rule)
    if min_confidence is not None:
        query = query.where(MultiEvent.confidence >= min_confidence)

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "count": len(events),
        "limit": limit,
        "offset": offset,
        "events": [
            {
                "event_id": str(event.event_id),
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "correlation_rule": event.correlation_rule,
                "source_events": event.source_events,
                "integrated_value": event.integrated_value,
                "confidence": event.confidence,
                "lineage": event.lineage,
            }
            for event in events
        ],
    }


@router.get("/mono/{event_id}")
async def get_mono_event_by_id(
    event_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Retrieve a specific mono-originated event by ID.

    Args:
        event_id: UUID of the event to retrieve
        db: Database session (injected)

    Returns:
        Event details

    Raises:
        HTTPException: 404 if event not found
    """
    result = await db.execute(select(MonoEvent).where(MonoEvent.event_id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail=f"Mono event {event_id} not found")

    return {
        "event_id": str(event.event_id),
        "timestamp": event.timestamp.isoformat(),
        "source_stream": event.source_stream,
        "event_type": event.event_type,
        "value": event.value,
        "metadata": event.metadata,
    }


@router.get("/multi/{event_id}")
async def get_multi_event_by_id(
    event_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Retrieve a specific multi-originated event by ID.

    Args:
        event_id: UUID of the event to retrieve
        db: Database session (injected)

    Returns:
        Event details with full lineage

    Raises:
        HTTPException: 404 if event not found
    """
    result = await db.execute(select(MultiEvent).where(MultiEvent.event_id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail=f"Multi event {event_id} not found")

    return {
        "event_id": str(event.event_id),
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "correlation_rule": event.correlation_rule,
        "source_events": event.source_events,
        "integrated_value": event.integrated_value,
        "confidence": event.confidence,
        "lineage": event.lineage,
    }


@router.get("/stats")
async def get_event_statistics(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get aggregate statistics about stored events.

    Args:
        db: Database session (injected)

    Returns:
        Statistical summary of events in the database
    """
    from sqlalchemy import func

    # Count mono events
    mono_count_result = await db.execute(select(func.count(MonoEvent.event_id)))
    mono_count = mono_count_result.scalar()

    # Count multi events
    multi_count_result = await db.execute(select(func.count(MultiEvent.event_id)))
    multi_count = multi_count_result.scalar()

    # Get time range for mono events
    mono_time_range = await db.execute(
        select(
            func.min(MonoEvent.timestamp),
            func.max(MonoEvent.timestamp),
        )
    )
    mono_earliest, mono_latest = mono_time_range.first()

    # Get time range for multi events
    multi_time_range = await db.execute(
        select(
            func.min(MultiEvent.timestamp),
            func.max(MultiEvent.timestamp),
        )
    )
    multi_earliest, multi_latest = multi_time_range.first()

    return {
        "mono_events": {
            "total_count": mono_count,
            "earliest": mono_earliest.isoformat() if mono_earliest else None,
            "latest": mono_latest.isoformat() if mono_latest else None,
        },
        "multi_events": {
            "total_count": multi_count,
            "earliest": multi_earliest.isoformat() if multi_earliest else None,
            "latest": multi_latest.isoformat() if multi_latest else None,
        },
        "integration_ratio": (
            round(multi_count / mono_count, 3) if mono_count > 0 else 0.0
        ),
    }
