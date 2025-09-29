"""API route modules for the Astrocyte Database API.

This package contains all route handlers organized by functionality:
- health: System health checks and diagnostics
- events: Historical event queries (PostgreSQL)
- stream: Real-time event streaming (Redis WebSocket)
"""

from . import events, health, stream

__all__ = ["health", "events", "stream"]
