"""Leaflet domain: Complex Event Processing for event integration."""

from collections import deque
from collections.abc import Generator
from datetime import datetime, timedelta

import redis

from . import config
from .types import CorrelationWindow, EventType, MonoOriginatedEvent, MultiOriginatedEvent


class LeafletDomain:
    """CEP engine implementing tripartite synapse integration.

    Uses deque for efficient event buffering and O(1) operations.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        window_seconds: float = config.CORRELATION_WINDOW_SECONDS
    ):
        """Initialize leaflet domain with event buffer.

        Args:
            redis_client: Redis connection
            window_seconds: Time window for event correlation
        """
        self.redis = redis_client
        self.window_seconds = window_seconds
        self.event_buffer: deque[MonoOriginatedEvent] = deque(
            maxlen=config.MAX_PENDING_EVENTS
        )
        self.correlation_rules: dict[str, CorrelationWindow] = self._init_correlation_rules()

    def _init_correlation_rules(self) -> dict[str, CorrelationWindow]:
        """Initialize event correlation rules.

        Returns:
            Dictionary of correlation rule name to window configuration
        """
        return {
            "type_A_and_B_within_window": CorrelationWindow(
                duration_seconds=self.window_seconds,
                required_event_types={EventType.TYPE_A, EventType.TYPE_B},
                min_events=2
            ),
            "type_A_B_C_convergence": CorrelationWindow(
                duration_seconds=self.window_seconds,
                required_event_types={EventType.TYPE_A, EventType.TYPE_B, EventType.TYPE_C},
                min_events=3
            )
        }

    def add_event(self, event: MonoOriginatedEvent) -> None:
        """Add event to buffer with automatic pruning.

        Args:
            event: Mono-originated event to buffer
        """
        self.event_buffer.append(event)
        self._prune_expired_events()

    def _prune_expired_events(self) -> None:
        """Remove events outside correlation window.

        Uses efficient deque operations for O(1) removal.
        """
        cutoff_time = datetime.now() - timedelta(seconds=self.window_seconds)
        while self.event_buffer and self.event_buffer[0].timestamp < cutoff_time:
            self.event_buffer.popleft()

    def check_correlation(self, rule_name: str) -> MultiOriginatedEvent | None:
        """Check if events in buffer satisfy correlation rule.

        Args:
            rule_name: Name of correlation rule to check

        Returns:
            MultiOriginatedEvent if correlation found, None otherwise
        """
        rule = self.correlation_rules.get(rule_name)
        if not rule:
            return None

        # Use set for O(1) membership testing
        event_types_found: set[EventType] = set()
        matching_events: list[MonoOriginatedEvent] = []

        for event in self.event_buffer:
            if event.event_type in rule.required_event_types:
                event_types_found.add(event.event_type)
                matching_events.append(event)

        # Check if correlation satisfied
        if (
            event_types_found >= rule.required_event_types
            and len(matching_events) >= rule.min_events
        ):
            return self._create_multi_originated_event(matching_events, rule_name)

        return None

    def _create_multi_originated_event(
        self,
        source_events: list[MonoOriginatedEvent],
        rule_name: str
    ) -> MultiOriginatedEvent:
        """Create integrated event from source events.

        Args:
            source_events: Events that triggered correlation
            rule_name: Name of correlation rule used

        Returns:
            MultiOriginatedEvent with integrated data
        """
        integrated_value = sum(e.value for e in source_events) / len(source_events)
        confidence = min(1.0, len(source_events) / 3.0)

        lineage = {
            event.source_stream: {
                "event_id": str(event.event_id),
                "timestamp": event.timestamp.isoformat(),
                "value": event.value
            }
            for event in source_events
        }

        return MultiOriginatedEvent(
            source_events=[e.event_id for e in source_events],
            correlation_rule=rule_name,
            integrated_value=integrated_value,
            confidence=confidence,
            lineage=lineage
        )


def process_stream_to_integration(
    redis_client: redis.Redis,
    stream_names: list[str],
    output_stream: str = config.STREAM_INTEGRATED
) -> Generator[MultiOriginatedEvent, None, None]:
    """Process input streams and yield integrated events.

    Uses generator for lazy evaluation and memory efficiency.

    Args:
        redis_client: Redis connection
        stream_names: List of input stream names
        output_stream: Stream to write integrated events

    Yields:
        MultiOriginatedEvent instances when correlations found
    """
    leaflet = LeafletDomain(redis_client)

    # Create consumer group if not exists
    for stream_name in stream_names:
        try:
            redis_client.xgroup_create(
                name=stream_name,
                groupname=config.CONSUMER_GROUP,
                id="0",
                mkstream=True
            )
        except redis.ResponseError:
            pass  # Group already exists

    # Read from streams and process
    streams_dict = {name: ">" for name in stream_names}

    while True:
        messages = redis_client.xreadgroup(
            groupname=config.CONSUMER_GROUP,
            consumername=config.CONSUMER_NAME_CEP,
            streams=streams_dict,  # type: ignore[arg-type]
            count=config.EVENT_BATCH_SIZE,
            block=1000
        )

        if not messages:
            continue

        for stream_name, events in messages:
            for event_id, event_data in events:
                # Parse mono-originated event using from_redis_dict method
                event_data_with_stream = dict(event_data)
                event_data_with_stream["source_stream"] = stream_name
                event = MonoOriginatedEvent.from_redis_dict(event_data_with_stream)

                leaflet.add_event(event)

                # Check all correlation rules
                for rule_name in leaflet.correlation_rules:
                    multi_event = leaflet.check_correlation(rule_name)
                    if multi_event:
                        # Write to output stream
                        redis_data = multi_event.to_redis_dict()
                        redis_client.xadd(output_stream, redis_data)  # type: ignore[arg-type]
                        yield multi_event

                # Acknowledge message
                redis_client.xack(stream_name, config.CONSUMER_GROUP, event_id)
