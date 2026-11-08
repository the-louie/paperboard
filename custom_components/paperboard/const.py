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

# Panel profile: "auto" (from the device's Model/Width/Height headers) or a TRMNL model name
# from models.json. The two early ids are kept as aliases for screens created before B-064.
PROFILE_AUTO = "auto"
PROFILE_ALIASES = {"800x480_1bit": "og_png", "800x480_2bit": "og_plus"}
DEFAULT_PROFILE = PROFILE_AUTO

# Dispatcher signal fired on every authenticated check-in; format with the screen id.
SIGNAL_CHECKIN = "paperboard_checkin_{}"
# Fired when a screen gets a new (different) frame; format with the screen id.
SIGNAL_FRAME = "paperboard_frame_{}"

CONF_ROLES = "roles"
# Role -> entity selector filter. Every role is optional; layouts degrade without it.
ROLE_FILTERS: dict[str, dict] = {
    "weather": {"domain": "weather"},
    "outdoor_temp": {"domain": "sensor", "device_class": "temperature"},
    "indoor_temp": {"domain": "sensor", "device_class": "temperature"},
    "feels_like": {"domain": "sensor", "device_class": "temperature"},
    "outdoor_humidity": {"domain": "sensor", "device_class": "humidity"},
    "rain_today": {"domain": "sensor"},
    "price": {"domain": "sensor"},
    "solar_forecast_today": {"domain": "sensor", "device_class": "energy"},
    "solar_power": {"domain": "sensor", "device_class": "power"},
    "grid_power": {"domain": "sensor", "device_class": "power"},
    "house_power": {"domain": "sensor", "device_class": "power"},
    "house_energy_today": {"domain": "sensor", "device_class": "energy"},
    "battery_soc": {"domain": "sensor", "device_class": "battery"},
    "battery_power": {"domain": "sensor", "device_class": "power"},
    "sun": {"domain": "sun"},
}
LIST_ROLES: dict[str, dict] = {
    "rooms": {"domain": "sensor", "device_class": "temperature"},
    "calendars": {"domain": "calendar"},
}
