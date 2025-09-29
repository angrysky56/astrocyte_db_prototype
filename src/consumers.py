"""Event consumers for monitoring integrated events."""

from collections.abc import Generator

import redis

from . import config
from .types import MultiOriginatedEvent


def monitor_integrated_events(
    redis_client: redis.Redis,
    stream_name: str = config.STREAM_INTEGRATED
) -> Generator[MultiOriginatedEvent, None, None]:
    """Monitor and yield integrated events from the leaflet domain.

    Uses generator for lazy evaluation and memory efficiency.

    Args:
        redis_client: Redis connection
        stream_name: Stream to monitor for integrated events

    Yields:
        MultiOriginatedEvent instances as they arrive
    """
    try:
        redis_client.xgroup_create(
            name=stream_name,
            groupname=config.CONSUMER_GROUP,
            id="0",
            mkstream=True
        )
    except redis.ResponseError:
        pass  # Group already exists

    last_id = ">"

    while True:
        messages = redis_client.xreadgroup(
            groupname=config.CONSUMER_GROUP,
            consumername=config.CONSUMER_NAME_MONITOR,
            streams={stream_name: last_id},  # type: ignore[arg-type]
            count=config.EVENT_BATCH_SIZE,
            block=1000
        )

        if not messages:
            continue

        for _, events in messages:
            for event_id, event_data in events:
                # Parse multi-originated event using from_redis_dict method
                event = MultiOriginatedEvent.from_redis_dict(event_data)

                yield event

                # Acknowledge message
                redis_client.xack(stream_name, config.CONSUMER_GROUP, event_id)


def print_event_summary(event: MultiOriginatedEvent) -> None:
    """Print a formatted summary of an integrated event.

    Args:
        event: MultiOriginatedEvent to display
    """
    print(f"\n{'=' * 80}")
    print("🧠 MULTI-ORIGINATED EVENT DETECTED")
    print(f"{'=' * 80}")
    print(f"Event ID:         {event.event_id}")
    print(f"Timestamp:        {event.timestamp.isoformat()}")
    print(f"Correlation Rule: {event.correlation_rule}")
    print(f"Integrated Value: {event.integrated_value:.2f}")
    print(f"Confidence:       {event.confidence:.2%}")
    print(f"\nSource Events ({len(event.source_events)}):")
    for stream, details in event.lineage.items():
        print(f"  • {stream}")
        print(f"    - Event ID:  {details['event_id']}")
        print(f"    - Timestamp: {details['timestamp']}")
        print(f"    - Value:     {details['value']:.2f}")
    print(f"{'=' * 80}\n")
