"""
Centralized configuration constants for S9Checker.
All magic numbers and defaults live here.
"""

# ---------------------------------------------------------------------------
# Network defaults
# ---------------------------------------------------------------------------
DEFAULT_DELAY = 0.3            # Seconds between requests per worker
DEFAULT_CONCURRENCY = 10       # Default max concurrent workers
DEFAULT_TIMEOUT = 15           # HTTP request timeout in seconds
MAX_RETRIES_429 = 3            # Max retries on HTTP 429
RETRY_BACKOFF_BASE = 3         # Exponential backoff multiplier (5s, 15s, 45s)
DEFAULT_RATE_LIMIT = 2.0       # Default requests per second per platform
HTTP_CONNECTOR_LIMIT = 50      # Max open connections in aiohttp pool

# ---------------------------------------------------------------------------
# File system
# ---------------------------------------------------------------------------
RESULTS_DIR = "results"
COMBOLIST_DIR = "combolists"
OUTPUT_ENCODING = "utf-8"

# ---------------------------------------------------------------------------
# Combo list parsing
# ---------------------------------------------------------------------------
MIN_COMBO_PARTS = 2            # Minimum parts after split(':')
REQUIRED_FIELDS = ("email", "password")

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
PROGRESS_UPDATE_INTERVAL = 0.2  # Seconds between progress callbacks
