"""Constants for the paperboard integration."""

DOMAIN = "paperboard"

CONF_BASE_URL = "base_url"
CONF_REFRESH_RATE = "refresh_rate"

DEFAULT_REFRESH_RATE = 900  # seconds; what the owner's device runs today
MIN_REFRESH_RATE = 60
MAX_REFRESH_RATE = 86_400
