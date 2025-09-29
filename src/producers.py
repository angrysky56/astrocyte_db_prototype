"""Event producers simulating synaptic inputs to Redis Streams."""

import random
import time
from collections.abc import Generator
from datetime import datetime

import redis

from . import config
from .types import EventType, MonoOriginatedEvent


def create_redis_client() -> redis.Redis:
    """Create and return a Redis client connection.

    Returns:
        Redis client with connection pooling
    """
    return redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=config.REDIS_DECODE_RESPONSES
    )


def generate_events(
    stream_name: str,
    event_type: EventType,
    interval_seconds: float = config.PRODUCER_EVENT_INTERVAL_SECONDS
) -> Generator[MonoOriginatedEvent, None, None]:
    """Generate mono-originated events with configurable interval.

    Uses lazy evaluation (generator) for memory efficiency.

    Args:
        stream_name: Redis stream to produce to
        event_type: Type of event to generate
        interval_seconds: Time between events

    Yields:
        MonoOriginatedEvent instances
    """
    while True:
        value = random.uniform(*config.PRODUCER_VALUE_RANGE)
        event = MonoOriginatedEvent(
            source_stream=stream_name,
            event_type=event_type,
            value=value,
            timestamp=datetime.now(),
            metadata={"producer_interval": interval_seconds}
        )
        yield event
        time.sleep(interval_seconds)
