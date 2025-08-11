"""Constants for the Sodisys integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "sodisys"

# Configuration keys
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_KINDERGARTEN_ZONE: Final = "kindergarten_zone"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_TIMEZONE: Final = "timezone"

# Default values
DEFAULT_UPDATE_INTERVAL: Final = 300  # 5 minutes
DEFAULT_KINDERGARTEN_ZONE: Final = "kindergarten"
# Common timezone for German kindergartens
DEFAULT_TIMEZONE: Final = "Europe/Berlin"

# Device tracker states
STATE_HOME: Final = "home"
STATE_NOT_HOME: Final = "not_home"

# Attributes
ATTR_CHILD_ID: Final = "child_id"
ATTR_CHECK_IN_TIME: Final = "check_in_time"
ATTR_CHECK_OUT_TIME: Final = "check_out_time"
ATTR_LAST_UPDATED: Final = "last_updated"

# Device info
DEVICE_MANUFACTURER: Final = "Sodisys"
DEVICE_MODEL_CHILD: Final = "Child"
DEVICE_SW_VERSION: Final = "0.1.0"

# Error messages
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_INVALID_AUTH: Final = "invalid_auth"
ERROR_UNKNOWN: Final = "unknown"
