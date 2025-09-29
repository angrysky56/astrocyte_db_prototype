"""Type definitions for astrocyte database events."""

import json
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Biological-inspired event classification."""

    # Mono-originated (simple synaptic inputs)
    TYPE_A = "A"
    TYPE_B = "B"
    TYPE_C = "C"

    # Multi-originated (integrated Ca²⁺ signals)
    MULTI_ORIGINATED = "MULTI_ORIGINATED"


class MonoOriginatedEvent(BaseModel):
    """Simple event from a single synaptic source."""

    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    source_stream: str
    event_type: EventType
    value: float
    metadata: dict[str, str | int | float] = Field(default_factory=dict)

    model_config = {"frozen": False}

    def to_redis_dict(self) -> dict[str, str]:
        """Convert to Redis-compatible dictionary with string values."""
        return {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "source_stream": self.source_stream,
            "event_type": self.event_type.value,
            "value": str(self.value),
            "metadata": json.dumps(self.metadata)
        }

    @classmethod
    def from_redis_dict(cls, data: dict[str, str]) -> "MonoOriginatedEvent":
        """Create instance from Redis dictionary."""
        return cls(
            event_id=UUID(data["event_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_stream=data["source_stream"],
            event_type=EventType(data["event_type"]),
            value=float(data["value"]),
            metadata=json.loads(data["metadata"]) if data.get("metadata") else {}
        )


class MultiOriginatedEvent(BaseModel):
    """Complex event integrated from multiple sources."""

    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: EventType = EventType.MULTI_ORIGINATED
    source_events: list[UUID]
    correlation_rule: str
    integrated_value: float
    confidence: float = Field(ge=0.0, le=1.0)
    lineage: dict[str, dict[str, str | float]]

    model_config = {"frozen": False}

    def to_redis_dict(self) -> dict[str, str]:
        """Convert to Redis-compatible dictionary with string values."""
        return {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "source_events": ",".join(str(uuid) for uuid in self.source_events),
            "correlation_rule": self.correlation_rule,
            "integrated_value": str(self.integrated_value),
            "confidence": str(self.confidence),
            "lineage": json.dumps(self.lineage)
        }

    @classmethod
    def from_redis_dict(cls, data: dict[str, str]) -> "MultiOriginatedEvent":
        """Create instance from Redis dictionary."""
        return cls(
            event_id=UUID(data["event_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_events=[UUID(uuid_str) for uuid_str in data["source_events"].split(",")],
            correlation_rule=data["correlation_rule"],
            integrated_value=float(data["integrated_value"]),
            confidence=float(data["confidence"]),
            lineage=json.loads(data["lineage"])
        )


class CorrelationWindow(BaseModel):
    """Time window for event correlation."""

    duration_seconds: float = Field(ge=0.1, le=60.0)
    required_event_types: set[EventType]
    min_events: int = Field(ge=2, le=10)

    model_config = {"frozen": False}
