"""HTTP views. Device-facing views authenticate themselves (requires_auth=False) and always
*return* error responses - never raise HTTPUnauthorized - so HA's ip_ban is untouched (T-03).
Responses are built directly so they are never gzip-compressed (the firmware cannot inflate).
"""

from __future__ import annotations

import hmac
import json
import time
from http import HTTPStatus

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_CHECKIN
from .devices import new_device
from .runtime import HubRuntime, ScreenRuntime

IMAGE_URL = "/api/paperboard/image/{screen_id}/{token}/{filename}"


def image_path(screen: ScreenRuntime, ext: str = "png") -> str:
    """Path of the screen's current image; the filename (content hash) only busts caches."""
    name = screen.frame.sha if screen.frame else "pending"
    return f"/api/paperboard/image/{screen.subentry_id}/{screen.image_token}/{name}.{ext}"


def base_url(hub: HubRuntime, request: web.Request) -> str:
    """Configured base URL, else the origin the device used to reach us."""
    return hub.base_url or f"{request.scheme}://{request.host}"


def _json(payload: dict) -> web.Response:
    """Uncompressed JSON (HomeAssistantView.json() gzips bodies over 1 kB)."""
    return web.Response(text=json.dumps(payload), content_type="application/json")


def _hub(hass: HomeAssistant) -> HubRuntime | None:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data
    return None


class ImageView(HomeAssistantView):
    """Serves a screen's current frame to devices and generic image clients."""

    url = IMAGE_URL
    name = "api:paperboard:image"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, screen_id: str, token: str,
                  filename: str) -> web.Response:
        """Current frame. aiohttp drops the body of HEAD responses but keeps the headers."""
        hub = _hub(self.hass)
        screen = hub.screens.get(screen_id) if hub else None
        if screen is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)
        if not hmac.compare_digest(token.encode(), screen.image_token.encode()):
            return web.Response(status=HTTPStatus.FORBIDDEN)
        if screen.frame is None:
            return web.Response(status=HTTPStatus.SERVICE_UNAVAILABLE,
                                headers={"Retry-After": "60"})
        etag = f'"{screen.frame.sha}"'
        headers = {"ETag": etag, "Cache-Control": "no-cache",
                   "X-Paperboard-Stale": "1" if screen.stale else "0"}
        if request.headers.get("If-None-Match") == etag:
            return web.Response(status=HTTPStatus.NOT_MODIFIED, headers=headers)
        if filename.endswith(".bmp"):
            return web.Response(body=screen.bmp(), content_type="image/bmp", headers=headers)
        return web.Response(body=screen.frame.png, content_type="image/png", headers=headers)

    async def head(self, request: web.Request, screen_id: str, token: str,
                   filename: str) -> web.Response:
        """HA registers only the methods a view defines."""
        return await self.get(request, screen_id, token, filename)


class SetupView(HomeAssistantView):
    """GET /api/setup: pairs a device, but only inside the window (docs/design/device-api.md)."""

    url = "/api/setup"
    name = "api:paperboard:setup"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        hub = _hub(self.hass)
        mac = request.headers.get("ID", "").strip()
        if hub is None or not mac:
            return _json({"status": 404, "message": "Missing device ID"})
        screen_id = hub.pairing_target()
        screen = hub.screens.get(screen_id) if screen_id else None
        if screen is None:
            return _json({"status": 404, "message": "Pairing is closed. Press Pair on the "
                                                    "screen in Home Assistant."})
        device = new_device(mac)
        hub.devices.bind(screen.subentry_id, device)
        hub.close_pairing()
        return _json({"status": 200, "api_key": device.api_key,
                      "friendly_id": device.friendly_id,
                      "image_url": base_url(hub, request) + image_path(screen, "bmp"),
                      "message": f"Paired with {screen.name}"})


# Firmware headers kept as telemetry (research notes, firmware 1.8.19; WiFi-Band and Wake-Time
# seen on the owner's 1.8.10). Never the Access-Token.
TELEMETRY_HEADERS = ("Battery-Voltage", "RSSI", "FW-Version", "Model", "Width", "Height",
                     "Refresh-Rate", "Image-Cached", "Wake-Time", "Reset-Reason", "WiFi-Band",
                     "Update-Source")


class DisplayView(HomeAssistantView):
    """GET /api/display: authenticated poll -> current image and refresh rate."""

    url = "/api/display"
    name = "api:paperboard:display"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        hub = _hub(self.hass)
        mac = request.headers.get("ID", "").strip().upper()
        token = request.headers.get("Access-Token", "")
        screen_id = hub.devices.screen_for_mac(mac) if hub and mac else None
        device = hub.devices.devices.get(screen_id) if hub and screen_id else None
        screen = hub.screens.get(screen_id) if hub and screen_id else None
        if (hub is None or device is None or screen is None
                or not hmac.compare_digest(token.encode(), device.api_key.encode())):
            if hub is not None:
                hub.last_rejected = {"mac": mac or "?", "ip": request.remote or "?",
                                     "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            # JSON status 500 without reset_firmware: the firmware drops its key and re-runs
            # setup (which only succeeds inside a pairing window). Never a full reset.
            return _json({"status": 500, "message": "Unknown device, re-running setup"})

        screen.telemetry = {h: request.headers[h] for h in TELEMETRY_HEADERS
                            if h in request.headers}
        screen.last_checkin = time.time()
        async_dispatcher_send(self.hass, SIGNAL_CHECKIN.format(screen.subentry_id))
        if screen.frame is None:
            return _json({"status": 202, "message": "No image rendered yet",
                          "refresh_rate": 60})
        return _json({"status": 0,
                      "image_url": base_url(hub, request) + image_path(screen),
                      "filename": screen.frame.sha,
                      "refresh_rate": screen.refresh_rate,
                      "update_firmware": False, "reset_firmware": False,
                      "special_function": "none"})
