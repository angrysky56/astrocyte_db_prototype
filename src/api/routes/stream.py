"""WebSocket streaming endpoints for real-time event monitoring.

Provides WebSocket connections for streaming events directly from Redis Streams
as they're produced, enabling real-time monitoring of the astrocyte system.
"""

import asyncio
import json
from typing import Literal

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from ... import config

router = APIRouter()


async def get_redis_client() -> Redis:
    """Create and return a Redis client for streaming.

    Returns:
        Redis: Async Redis client connected to configured instance
    """
    return Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=True,
    )


@router.websocket("/ws")
async def websocket_event_stream(
    websocket: WebSocket,
    stream: Literal["mono", "multi", "all"] = "all",
    source: str | None = None,
) -> None:
    """WebSocket endpoint for real-time event streaming.

    Args:
        websocket: WebSocket connection
        stream: Type of events to stream ('mono', 'multi', or 'all')
        source: Optional source stream filter (for mono events)

    Query Parameters:
        - stream: Event type filter (default: 'all')
        - source: Source stream filter (e.g., 'stream:axon_1')

    Example:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/stream/ws?stream=mono&source=stream:axon_1');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Event received:', data);
        };
        ```
    """
    await websocket.accept()
    redis = await get_redis_client()

    try:
        # Determine which streams to monitor
        streams_to_monitor = []

        if stream in ("mono", "all"):
            if source:
                # Monitor specific source stream
                streams_to_monitor.append(source)
            else:
                # Monitor all mono-originated streams
                streams_to_monitor.extend(
                    [config.STREAM_AXON_1, config.STREAM_AXON_2, config.STREAM_AXON_3]
                )

        if stream in ("multi", "all"):
            # Monitor integrated events stream
            streams_to_monitor.append(config.STREAM_INTEGRATED)

        # Initialize stream positions (start from latest)
        stream_positions = {stream_name: "$" for stream_name in streams_to_monitor}

        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "monitoring": streams_to_monitor,
            }
        )

        # Stream events in real-time
        while True:
            # Read from all monitored streams
            messages = await redis.xread(
                streams=stream_positions,
                count=10,
                block=100,  # Block for 100ms if no messages
            )

            if messages:
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        # Update position for this stream
                        stream_positions[stream_name] = message_id

                        # Parse and send the event
                        event = {
                            "stream": stream_name,
                            "message_id": message_id,
                            "data": message_data,
                            "timestamp": message_data.get("timestamp"),
                        }

                        await websocket.send_json(event)

            # Allow other tasks to run
            await asyncio.sleep(0)

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Send error to client before closing
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"Stream error: {str(e)}",
                }
            )
        except Exception:
            pass
    finally:
        await redis.aclose()


@router.websocket("/ws/stats")
async def websocket_stats_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time system statistics.

    Streams aggregate statistics about event processing rates,
    correlation efficiency, and system health.

    Args:
        websocket: WebSocket connection

    Example:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/stream/ws/stats');
        ws.onmessage = (event) => {
            const stats = JSON.parse(event.data);
            console.log('System stats:', stats);
        };
        ```
    """
    await websocket.accept()
    redis = await get_redis_client()

    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "description": "Real-time system statistics",
            }
        )

        while True:
            # Gather statistics from Redis
            stats = {}

            # Get stream lengths
            for stream_name in [
                config.STREAM_AXON_1,
                config.STREAM_AXON_2,
                config.STREAM_AXON_3,
                config.STREAM_INTEGRATED,
            ]:
                length = await redis.xlen(stream_name)
                stats[stream_name] = {"pending_events": length}

            # Calculate integration ratio (multi vs. mono events)
            mono_total = sum(
                stats[s]["pending_events"]
                for s in [
                    config.STREAM_AXON_1,
                    config.STREAM_AXON_2,
                    config.STREAM_AXON_3,
                ]
            )
            multi_total = stats[config.STREAM_INTEGRATED]["pending_events"]

            stats["integration_ratio"] = (
                round(multi_total / mono_total, 3) if mono_total > 0 else 0.0
            )

            # Send statistics
            await websocket.send_json(
                {
                    "type": "stats",
                    "timestamp": asyncio.get_event_loop().time(),
                    "streams": stats,
                }
            )

            # Update every second
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"Stats stream error: {str(e)}",
                }
            )
        except Exception:
            pass
    finally:
        await redis.aclose()
