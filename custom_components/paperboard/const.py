"""Constants for the paperboard integration."""

DOMAIN = "paperboard"

CONF_BASE_URL = "base_url"
CONF_REFRESH_RATE = "refresh_rate"

DEFAULT_REFRESH_RATE = 900  # seconds; what the owner's device runs today
MIN_REFRESH_RATE = 60
MAX_REFRESH_RATE = 86_400

SUBENTRY_SCREEN = "screen"
CONF_NAME = "name"
CONF_PROFILE = "profile"
CONF_LAYOUT = "layout"
CONF_MAC = "mac"
CONF_API_KEY = "api_key"
CONF_IMAGE_TOKEN = "image_token"

DEFAULT_LAYOUT = "tidslinjen"

# Panel profiles: id -> (width, height, bit depth, byte limit). Extended in phase 4 (B-064).
PROFILES: dict[str, tuple[int, int, int, int]] = {
    "800x480_1bit": (800, 480, 1, 90_000),
    "800x480_2bit": (800, 480, 2, 90_000),
}
DEFAULT_PROFILE = "800x480_1bit"

# Dispatcher signal fired on every authenticated check-in; format with the screen id.
SIGNAL_CHECKIN = "paperboard_checkin_{}"
# Fired when a screen gets a new (different) frame; format with the screen id.
SIGNAL_FRAME = "paperboard_frame_{}"
