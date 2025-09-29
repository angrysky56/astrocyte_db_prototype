"""Configuration constants for the astrocyte database prototype."""

from pathlib import Path

# Redis connection
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_DECODE_RESPONSES = True

# PostgreSQL connection
POSTGRES_USER = "astrocyte"
POSTGRES_PASSWORD = "astrocyte_dev_password"
POSTGRES_DB = "astrocyte_db"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432

# Construct PostgreSQL URL for async SQLAlchemy
POSTGRES_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Database connection pool settings
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
SQL_ECHO = False  # Set to True for SQL query logging

# Stream names (biological: axons transmitting signals)
STREAM_AXON_1 = "stream:axon_1"
STREAM_AXON_2 = "stream:axon_2"
STREAM_AXON_3 = "stream:axon_3"
STREAM_INTEGRATED = "stream:integrated_events"

# Consumer group (biological: leaflet domain processing cluster)
CONSUMER_GROUP = "leaflet_domain_group"
CONSUMER_NAME_CEP = "cep_processor"
CONSUMER_NAME_MONITOR = "event_monitor"

# Event correlation parameters
CORRELATION_WINDOW_SECONDS = 2.0
EVENT_BATCH_SIZE = 10
MAX_PENDING_EVENTS = 100

# Storage management (Redis → PostgreSQL archival)
ARCHIVAL_INTERVAL_SECONDS = 60  # How often to archive events
REDIS_TTL_SECONDS = 300  # Keep events in Redis for 5 minutes
MAX_EVENTS_PER_ARCHIVE_BATCH = 1000  # Maximum events to archive per batch

# Producer simulation parameters
PRODUCER_EVENT_INTERVAL_SECONDS = 0.5
PRODUCER_VALUE_RANGE = (0, 100)

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "Astrocyte Database API"
API_VERSION = "0.2.0"

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
