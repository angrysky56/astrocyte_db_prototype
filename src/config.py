"""Configuration constants for the astrocyte database prototype."""

from pathlib import Path

# Redis connection
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_DECODE_RESPONSES = True

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

# Producer simulation parameters
PRODUCER_EVENT_INTERVAL_SECONDS = 0.5
PRODUCER_VALUE_RANGE = (0, 100)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
