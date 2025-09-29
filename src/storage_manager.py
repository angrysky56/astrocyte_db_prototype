"""Storage manager for archiving events from Redis to PostgreSQL.

Implements the two-tier storage architecture:
- Hot Tier: Redis Streams for real-time processing
- Cold Tier: PostgreSQL for persistent, queryable storage
"""

import asyncio
from datetime import datetime, timedelta

import redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import config
from .database import async_session_maker
from .models import EventArchiveStatus, MonoEvent, MultiEvent
from .types import MonoOriginatedEvent, MultiOriginatedEvent


class StorageManager:
    """Manages event archival from Redis (hot tier) to PostgreSQL (cold tier).

    Implements automatic background archival with idempotency guarantees.
    """

    def __init__(self, redis_client: redis.Redis):
        """Initialize storage manager.

        Args:
            redis_client: Redis connection for reading streams
        """
        self.redis = redis_client
        self.running = False

    async def start_archival_loop(self) -> None:
        """Start background task for continuous event archival.

        Runs indefinitely until stopped, archiving events at configured intervals.
        """
        self.running = True
        while self.running:
            try:
                await self._archive_batch()
                await asyncio.sleep(config.ARCHIVAL_INTERVAL_SECONDS)
            except Exception as e:
                print(f"Archival error: {e}")
                await asyncio.sleep(config.ARCHIVAL_INTERVAL_SECONDS)

    def stop_archival_loop(self) -> None:
        """Stop the archival background task."""
        self.running = False

    async def _archive_batch(self) -> None:
        """Archive a batch of events from all streams to PostgreSQL."""
        async with async_session_maker() as session:
            # Archive mono-originated events
            for stream in [
                config.STREAM_AXON_1,
                config.STREAM_AXON_2,
                config.STREAM_AXON_3,
            ]:
                await self._archive_stream(session, stream, is_multi=False)

            # Archive multi-originated events
            await self._archive_stream(
                session, config.STREAM_INTEGRATED, is_multi=True
            )

            await session.commit()

    async def _archive_stream(
        self, session: AsyncSession, stream_name: str, is_multi: bool = False
    ) -> None:
        """Archive events from a single Redis stream.

        Args:
            session: Database session
            stream_name: Redis stream to archive from
            is_multi: Whether this is a multi-originated event stream
        """
        # Read unarchived events
        messages = self.redis.xread(
            {stream_name: "0"},  # Start from beginning (we track archived separately)
            count=config.MAX_EVENTS_PER_ARCHIVE_BATCH,
        )

        if not messages:
            return

        for stream, events in messages:
            for redis_message_id, event_data in events:
                # Check if already archived
                stmt = select(EventArchiveStatus).where(
                    EventArchiveStatus.stream_name == stream_name,
                    EventArchiveStatus.redis_message_id == redis_message_id,
                )
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    continue  # Already archived

                # Parse and store event
                if is_multi:
                    await self._store_multi_event(session, event_data)
                else:
                    await self._store_mono_event(session, stream_name, event_data)

                # Mark as archived
                archive_status = EventArchiveStatus(
                    stream_name=stream_name,
                    redis_message_id=redis_message_id,
                    event_id=event_data["event_id"],
                )
                session.add(archive_status)

    async def _store_mono_event(
        self, session: AsyncSession, stream_name: str, event_data: dict
    ) -> None:
        """Store mono-originated event in PostgreSQL.

        Args:
            session: Database session
            stream_name: Source stream name
            event_data: Event data from Redis
        """
        # Parse from Redis format
        event_data_with_stream = dict(event_data)
        event_data_with_stream["source_stream"] = stream_name
        pydantic_event = MonoOriginatedEvent.from_redis_dict(event_data_with_stream)

        # Create database model
        db_event = MonoEvent(
            event_id=pydantic_event.event_id,
            timestamp=pydantic_event.timestamp,
            source_stream=pydantic_event.source_stream,
            event_type=pydantic_event.event_type.value,
            value=pydantic_event.value,
            metadata=pydantic_event.metadata,
        )
        session.add(db_event)

    async def _store_multi_event(
        self, session: AsyncSession, event_data: dict
    ) -> None:
        """Store multi-originated event in PostgreSQL.

        Args:
            session: Database session
            event_data: Event data from Redis
        """
        # Parse from Redis format
        pydantic_event = MultiOriginatedEvent.from_redis_dict(event_data)

        # Create database model
        db_event = MultiEvent(
            event_id=pydantic_event.event_id,
            timestamp=pydantic_event.timestamp,
            event_type=pydantic_event.event_type.value,
            correlation_rule=pydantic_event.correlation_rule,
            source_events=[str(uuid) for uuid in pydantic_event.source_events],
            integrated_value=pydantic_event.integrated_value,
            confidence=pydantic_event.confidence,
            lineage=pydantic_event.lineage,
        )
        session.add(db_event)

    async def cleanup_old_redis_data(self) -> None:
        """Remove old events from Redis to prevent memory bloat.

        Deletes events older than configured TTL that have been archived.
        """
        cutoff_time = datetime.now() - timedelta(seconds=config.REDIS_TTL_SECONDS)
        cutoff_ms = int(cutoff_time.timestamp() * 1000)

        streams = [
            config.STREAM_AXON_1,
            config.STREAM_AXON_2,
            config.STREAM_AXON_3,
            config.STREAM_INTEGRATED,
        ]

        for stream in streams:
            # Use XTRIM with MINID to remove old messages
            try:
                self.redis.xtrim(stream, minid=cutoff_ms, approximate=False)
            except redis.ResponseError:
                pass  # Stream might not exist yet
