#!/usr/bin/env python3
"""End-to-end demonstration of the astrocyte database prototype.

This script demonstrates the complete workflow:
1. Synaptic inputs (producers) generate mono-originated events
2. Leaflet domain (CEP) integrates events into multi-originated events
3. Consumers monitor and display integrated events
"""

import sys
import threading
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import config
from src.consumers import monitor_integrated_events, print_event_summary
from src.leaflet_domain import process_stream_to_integration
from src.producers import create_redis_client, generate_events
from src.types import EventType


def produce_events(redis_client, stream_name, event_type, duration_seconds=30):
    """Producer thread function.

    Args:
        redis_client: Redis connection
        stream_name: Stream to produce to
        event_type: Type of events to generate
        duration_seconds: How long to produce events
    """
    print(f"🔄 Producer started: {stream_name} → {event_type}")

    event_generator = generate_events(stream_name, event_type, interval_seconds=0.3)
    start_time = time.time()

    try:
        for event in event_generator:
            if time.time() - start_time > duration_seconds:
                break

            redis_client.xadd(
                stream_name,
                event.to_redis_dict()
            )
            print(f"  📤 {stream_name}: {event.event_type} = {event.value:.2f}")

    except KeyboardInterrupt:
        pass

    print(f"✅ Producer stopped: {stream_name}")


def consume_integrated_events(redis_client, duration_seconds=30):
    """Consumer thread function.

    Args:
        redis_client: Redis connection
        duration_seconds: How long to consume events
    """
    print("🔍 Consumer started: monitoring integrated events\n")

    event_generator = monitor_integrated_events(redis_client)
    start_time = time.time()
    event_count = 0

    try:
        for event in event_generator:
            if time.time() - start_time > duration_seconds:
                break

            print_event_summary(event)
            event_count += 1

    except KeyboardInterrupt:
        pass

    print(f"\n✅ Consumer stopped: {event_count} integrated events detected")


def process_integration(redis_client, duration_seconds=30):
    """CEP processor thread function.

    Args:
        redis_client: Redis connection
        duration_seconds: How long to process
    """
    print("🧠 Leaflet domain started: processing event correlations\n")

    stream_names = [config.STREAM_AXON_1, config.STREAM_AXON_2, config.STREAM_AXON_3]
    integration_generator = process_stream_to_integration(redis_client, stream_names)
    start_time = time.time()
    integration_count = 0

    try:
        for _ in integration_generator:
            if time.time() - start_time > duration_seconds:
                break
            integration_count += 1

    except KeyboardInterrupt:
        pass

    print(f"✅ Leaflet domain stopped: {integration_count} integrations created")


def main():
    """Run complete astrocyte database demonstration."""
    print("=" * 80)
    print("🧠 ASTROCYTE DATABASE PROTOTYPE - LIVE DEMONSTRATION")
    print("=" * 80)
    print("\nArchitecture:")
    print("  Synaptic Inputs → Redis Streams → Leaflet Domain → Integrated Events")
    print("  (Producers)       (Hot Tier)      (CEP Engine)     (Output Stream)")
    print("\n" + "=" * 80 + "\n")

    redis_client = create_redis_client()

    try:
        redis_client.ping()
        print("✅ Redis connection established\n")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\nPlease ensure Redis is running:")
        print("  docker compose up -d")
        return 1

    demo_duration = 30

    # Start all threads
    threads = [
        threading.Thread(
            target=produce_events,
            args=(redis_client, config.STREAM_AXON_1, EventType.TYPE_A, demo_duration),
            daemon=True
        ),
        threading.Thread(
            target=produce_events,
            args=(redis_client, config.STREAM_AXON_2, EventType.TYPE_B, demo_duration),
            daemon=True
        ),
        threading.Thread(
            target=produce_events,
            args=(redis_client, config.STREAM_AXON_3, EventType.TYPE_C, demo_duration),
            daemon=True
        ),
        threading.Thread(
            target=process_integration,
            args=(redis_client, demo_duration),
            daemon=True
        ),
        threading.Thread(
            target=consume_integrated_events,
            args=(redis_client, demo_duration),
            daemon=True
        )
    ]

    for thread in threads:
        thread.start()

    # Wait for demo to complete
    try:
        time.sleep(demo_duration)
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")

    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
