"""SQLAlchemy models for persistent event storage.

These models provide the schema for storing events in PostgreSQL + TimescaleDB,
maintaining the biological metaphor while adding queryable persistence.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class MonoEvent(Base):
    """Mono-originated event: Simple synaptic input from single source.

    Maps to MonoOriginatedEvent from types.py but with database persistence.
    """

    __tablename__ = "mono_events"

    # Primary key
    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, index=True
    )

    # Temporal data (optimized for time-series queries)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Event classification
    source_stream: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Event data
    value: Mapped[float] = mapped_column(Float, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("idx_mono_timestamp_source", "timestamp", "source_stream"),
        Index("idx_mono_timestamp_type", "timestamp", "event_type"),
        Index("idx_mono_source_type", "source_stream", "event_type"),
    )


class MultiEvent(Base):
    """Multi-originated event: Integrated Ca²⁺ signal from multiple sources.

    Maps to MultiOriginatedEvent from types.py but with database persistence.
    """

    __tablename__ = "multi_events"

    # Primary key
    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, index=True
    )

    # Temporal data
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Event classification
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Correlation metadata
    correlation_rule: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_events: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # Integrated data
    integrated_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    lineage: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("idx_multi_timestamp_rule", "timestamp", "correlation_rule"),
        Index("idx_multi_timestamp_confidence", "timestamp", "confidence"),
        Index("idx_multi_rule_confidence", "correlation_rule", "confidence"),
    )


class EventArchiveStatus(Base):
    """Track archival status to prevent duplicate processing.

    Ensures idempotency when archiving events from Redis to PostgreSQL.
    """

    __tablename__ = "event_archive_status"

    # Composite primary key (stream + Redis message ID)
    stream_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    redis_message_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Archival metadata
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    event_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Index for cleanup queries
    __table_args__ = (
        Index("idx_archive_archived_at", "archived_at"),
        UniqueConstraint("stream_name", "redis_message_id", name="uix_stream_message"),
    )
