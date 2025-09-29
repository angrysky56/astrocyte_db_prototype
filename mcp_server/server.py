"""
Astrocyte DB MCP Server

A Model Context Protocol server for interacting with the Astrocyte Database prototype.
Provides tools for querying events, managing services, and monitoring system health.
"""

import asyncio
import json
import logging
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP

# Configure logging to stderr for MCP servers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("astrocyte-db")

# Configuration
API_BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).parent.parent
DOCKER_COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"

# Global HTTP client
http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client for API requests."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)
    return http_client


@mcp.tool()
async def query_mono_events(
    ctx: Context,
    limit: int = 10,
    offset: int = 0,
    start_time: str | None = None,
    end_time: str | None = None,
    source_stream: str | None = None,
    event_type: str | None = None,
) -> str:
    """
    Query mono-originated events from the database.

    Args:
        limit: Maximum number of events to return (default: 10)
        offset: Number of events to skip (default: 0)
        start_time: Filter events after this timestamp (ISO format)
        end_time: Filter events before this timestamp (ISO format)
        source_stream: Filter by source stream name
        event_type: Filter by event type

    Returns:
        JSON string with query results
    """
    try:
        client = await get_http_client()
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if source_stream:
            params["source_stream"] = source_stream
        if event_type:
            params["event_type"] = event_type

        response = await client.get("/events/mono", params=params)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Retrieved {len(data.get('events', []))} mono events")
        return json.dumps(data, indent=2)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error querying mono events: {e}")
        return json.dumps({"error": str(e), "type": "http_error"})
    except Exception as e:
        logger.error(f"Error querying mono events: {e}")
        return json.dumps({"error": str(e), "type": "unexpected_error"})


@mcp.tool()
async def query_multi_events(
    ctx: Context,
    limit: int = 10,
    offset: int = 0,
    start_time: str | None = None,
    end_time: str | None = None,
    correlation_rule: str | None = None,
    min_confidence: float | None = None,
) -> str:
    """
    Query multi-originated integrated events from the database.

    Args:
        limit: Maximum number of events to return (default: 10)
        offset: Number of events to skip (default: 0)
        start_time: Filter events after this timestamp (ISO format)
        end_time: Filter events before this timestamp (ISO format)
        correlation_rule: Filter by correlation rule name
        min_confidence: Minimum confidence score (0.0-1.0)

    Returns:
        JSON string with query results
    """
    try:
        client = await get_http_client()
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if correlation_rule:
            params["correlation_rule"] = correlation_rule
        if min_confidence is not None:
            params["min_confidence"] = min_confidence

        response = await client.get("/events/multi", params=params)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Retrieved {len(data.get('events', []))} multi events")
        return json.dumps(data, indent=2)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error querying multi events: {e}")
        return json.dumps({"error": str(e), "type": "http_error"})
    except Exception as e:
        logger.error(f"Error querying multi events: {e}")
        return json.dumps({"error": str(e), "type": "unexpected_error"})


@mcp.tool()
async def get_event_statistics(ctx: Context) -> str:
    """
    Get aggregate statistics about events in the database.

    Returns:
        JSON string with event counts and system statistics
    """
    try:
        client = await get_http_client()
        response = await client.get("/events/stats")
        response.raise_for_status()

        data = response.json()
        logger.info("Retrieved event statistics")
        return json.dumps(data, indent=2)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error getting statistics: {e}")
        return json.dumps({"error": str(e), "type": "http_error"})
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return json.dumps({"error": str(e), "type": "unexpected_error"})


@mcp.tool()
async def check_system_health(ctx: Context, full: bool = True) -> str:
    """
    Check the health status of all system components.

    Args:
        full: If True, performs comprehensive health check (default: True)

    Returns:
        JSON string with health status of all components
    """
    try:
        client = await get_http_client()
        endpoint = "/health/full" if full else "/health/"
        response = await client.get(endpoint)
        response.raise_for_status()

        data = response.json()
        logger.info(f"System health check: {data.get('status', 'unknown')}")
        return json.dumps(data, indent=2)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error checking health: {e}")
        return json.dumps({"error": str(e), "type": "http_error"})
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        return json.dumps({"error": str(e), "type": "unexpected_error"})


@mcp.tool()
async def manage_docker_services(
    ctx: Context,
    action: str,
    service: str | None = None,
) -> str:
    """
    Manage Docker Compose services for the Astrocyte DB.

    Args:
        action: Action to perform (up, down, restart, ps, logs)
        service: Specific service name (optional, applies to all if not specified)

    Returns:
        JSON string with command output
    """
    try:
        if not DOCKER_COMPOSE_PATH.exists():
            return json.dumps(
                {
                    "error": "docker-compose.yml not found",
                    "path": str(DOCKER_COMPOSE_PATH),
                }
            )

        # Build docker-compose command
        cmd = ["docker-compose", "-f", str(DOCKER_COMPOSE_PATH)]

        if action == "up":
            cmd.extend(["up", "-d"])
            if service:
                cmd.append(service)
        elif action == "down":
            cmd.append("down")
        elif action == "restart":
            cmd.append("restart")
            if service:
                cmd.append(service)
        elif action == "ps":
            cmd.append("ps")
        elif action == "logs":
            cmd.extend(["logs", "--tail=50"])
            if service:
                cmd.append(service)
        else:
            return json.dumps(
                {
                    "error": f"Unknown action: {action}",
                    "valid_actions": ["up", "down", "restart", "ps", "logs"],
                }
            )

        # Execute command
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        logger.info(f"Docker command executed: {' '.join(cmd)}")

        return json.dumps(
            {
                "action": action,
                "service": service,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
            indent=2,
        )

    except subprocess.TimeoutExpired:
        logger.error("Docker command timed out")
        return json.dumps({"error": "Command timed out", "type": "timeout"})
    except Exception as e:
        logger.error(f"Error managing Docker services: {e}")
        return json.dumps({"error": str(e), "type": "unexpected_error"})


@mcp.tool()
async def get_specific_event(
    ctx: Context,
    event_id: str,
    event_type: str = "mono",
) -> str:
    """
    Get a specific event by its UUID.

    Args:
        event_id: The UUID of the event
        event_type: Type of event ('mono' or 'multi', default: 'mono')

    Returns:
        JSON string with event details
    """
    try:
        client = await get_http_client()
        endpoint = f"/events/{event_type}/{event_id}"
        response = await client.get(endpoint)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Retrieved {event_type} event: {event_id}")
        return json.dumps(data, indent=2)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error getting event: {e}")
        return json.dumps({"error": str(e), "type": "http_error"})
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        return json.dumps({"error": str(e), "type": "unexpected_error"})


@mcp.resource("astrocyte://health")
async def health_resource() -> str:
    """
    Provides current system health status as a resource.

    Returns:
        System health status as text
    """
    try:
        client = await get_http_client()
        response = await client.get("/health/full")
        response.raise_for_status()
        data = response.json()

        # Format health status as readable text
        status_text = f"""Astrocyte DB System Health
Status: {data.get('status', 'unknown')}
Timestamp: {datetime.now().isoformat()}

Components:
- API: {data.get('api', {}).get('status', 'unknown')}
- Redis: {data.get('redis', {}).get('status', 'unknown')}
- Database: {data.get('database', {}).get('status', 'unknown')}
"""
        return status_text

    except Exception as e:
        logger.error(f"Error getting health resource: {e}")
        return f"Error retrieving health status: {e}"


@mcp.resource("astrocyte://stats")
async def stats_resource() -> str:
    """
    Provides current event statistics as a resource.

    Returns:
        Event statistics as text
    """
    try:
        client = await get_http_client()
        response = await client.get("/events/stats")
        response.raise_for_status()
        data = response.json()

        # Format statistics as readable text
        stats_text = f"""Astrocyte DB Event Statistics
Timestamp: {datetime.now().isoformat()}

Event Counts:
- Mono Events: {data.get('mono_event_count', 0)}
- Multi Events: {data.get('multi_event_count', 0)}
- Total Events: {data.get('total_event_count', 0)}

System Status: {data.get('status', 'unknown')}
"""
        return stats_text

    except Exception as e:
        logger.error(f"Error getting stats resource: {e}")
        return f"Error retrieving statistics: {e}"


@mcp.prompt()
def test_database_prompt(query_description: str) -> str:
    """
    Generate a prompt for testing the Astrocyte DB with specific queries.

    Args:
        query_description: Description of what to test

    Returns:
        Formatted prompt for testing
    """
    return f"""Let's test the Astrocyte Database with the following:

Test Description: {query_description}

Steps to perform:
1. Check system health with check_system_health()
2. Get current statistics with get_event_statistics()
3. Query relevant events based on the test description
4. Analyze the results and report any issues

Use the appropriate query tools (query_mono_events or query_multi_events) based on the test needs."""


@mcp.prompt()
def analyze_correlations_prompt(time_range: str) -> str:
    """
    Generate a prompt for analyzing event correlations.

    Args:
        time_range: Time range to analyze (e.g., "last hour", "today")

    Returns:
        Formatted prompt for correlation analysis
    """
    return f"""Analyze event correlations in the Astrocyte Database for {time_range}:

Analysis Steps:
1. Query multi-originated events using query_multi_events()
2. Examine correlation rules and confidence scores
3. Identify patterns in event integration
4. Look for any anomalies or unexpected correlations

Focus on:
- Correlation rule effectiveness
- Confidence score distributions
- Timing patterns in event correlation
- Source event relationships

Use filters to narrow down to specific correlation rules if needed."""


# Cleanup handlers
async def cleanup() -> None:
    """Clean up resources on shutdown."""
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None
    logger.info("Astrocyte DB MCP server shutdown complete")


def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully")
    asyncio.create_task(cleanup())
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    try:
        logger.info("Starting Astrocyte DB MCP server")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        asyncio.run(cleanup())
