"""HTTP views. Device-facing views authenticate themselves (requires_auth=False) and always
*return* error responses - never raise HTTPUnauthorized - so HA's ip_ban is untouched (T-03).
Responses are built directly so they are never gzip-compressed (the firmware cannot inflate).
"""

from __future__ import annotations

import hmac
import json
import time
from http import HTTPStatus
from ipaddress import ip_address

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.network import is_cloud_connection
from homeassistant.util import dt as dt_util
from homeassistant.util.network import is_local

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


def from_local_network(hass: HomeAssistant, request: web.Request) -> bool:
    """True for LAN/loopback clients that did not come in through Nabu Casa."""
    if is_cloud_connection(hass):
        return False
    try:
        return is_local(ip_address(request.remote or ""))
    except ValueError:
        return False


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
        known = False
        if screen_id is None:
            # B-094: a panel this hub already paired (factory reset, lost key) re-pairs to its
            # own screen without a window, so the owner never has to press Pair again. It gets
            # a fresh key; the old one stops working. LAN-only like every pairing.
            screen_id = hub.devices.screen_for_mac(mac)
            known = screen_id is not None
        screen = hub.screens.get(screen_id) if screen_id else None
        if screen is not None and not from_local_network(self.hass, request):
            # The views are reachable through every HA URL (Nabu Casa, proxies). Pairing hands
            # out a key that reveals the dashboard, so only devices on the LAN may pair.
            return _json({"status": 404, "message": "Pairing is only allowed from the "
                                                    "local network."})
        if screen is None:
            return _json({"status": 404, "message": "Pairing is closed. Press Pair on the "
                                                    "screen in Home Assistant."})
        device = new_device(mac)
        hub.devices.bind(screen.subentry_id, device)
        if not known:
            hub.close_pairing()
        return _json({"status": 200, "api_key": device.api_key,
                      "friendly_id": device.friendly_id,
                      "image_url": base_url(hub, request) + image_path(screen, "bmp"),
                      "message": f"Paired with {screen.name}"})


# Firmware headers kept as telemetry (research notes, firmware 1.8.19; WiFi-Band and Wake-Time
# seen on the owner's 1.8.10). Never the Access-Token.
# Update-Source values the TRMNL firmware sends after a button wake
# (usetrmnl/firmware lib/trmnl/src/logging_parsers.cpp: GPIO -> "button", EXT0/EXT1 on S3).
BUTTON_SOURCES = frozenset({"button", "EXT0", "EXT1"})
TELEMETRY_HEADERS = ("Battery-Voltage", "RSSI", "FW-Version", "Model", "Width", "Height",
                     "Refresh-Rate", "Image-Cached", "Wake-Time", "Reset-Reason", "WiFi-Band",
                     "Update-Source")


def _authenticated_screen(hub: HubRuntime | None, request: web.Request) -> ScreenRuntime | None:
    """The screen whose paired device matches the ID + Access-Token headers."""
    mac = request.headers.get("ID", "").strip().upper()
    token = request.headers.get("Access-Token", "")
    screen_id = hub.devices.screen_for_mac(mac) if hub and mac else None
    device = hub.devices.devices.get(screen_id) if hub and screen_id else None
    if device is None or not hmac.compare_digest(token.encode(), device.api_key.encode()):
        return None
    return hub.screens.get(screen_id)


def _refresh_rate(hass: HomeAssistant, hub: HubRuntime, screen: ScreenRuntime) -> int:
    """The screen's rate, shortened so the device wakes just after the next schedule switch."""
    renderer = hub.renderers.get(screen.subentry_id)
    now = dt_util.now()
    rate = screen.refresh_rate
    schedule = getattr(getattr(renderer, "layout", None), "schedule", None)
    if schedule is not None:
        states = {e: {"state": s.state} for e in schedule.conditions
                  if (s := hass.states.get(e)) is not None}
        rate = schedule.refresh_rate(now, states, screen.refresh_rate)
    if renderer is not None and renderer.held_layout(now) is not None:
        # Wake just after a button hold ends, so the schedule comes back on time.
        until = int((renderer.held[1] - now).total_seconds()) + 30
        rate = max(60, min(rate, until))
    return rate


class DisplayView(HomeAssistantView):
    """GET /api/display: authenticated poll -> current image and refresh rate."""

    url = "/api/display"
    name = "api:paperboard:display"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        hub = _hub(self.hass)
        if hub is None:
            # Not loaded (starting, or setup failed): never tell a paired device it is unknown,
            # or it drops its key and needs pairing again. Ask it to come back in a minute.
            return _json({"status": 202, "message": "Paperboard is not ready",
                          "refresh_rate": 60})
        screen = _authenticated_screen(hub, request)
        if screen is None:
            mac = request.headers.get("ID", "").strip().upper()
            hub.last_rejected = {"mac": mac or "?", "ip": request.remote or "?",
                                 "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            # JSON status 500 without reset_firmware: the firmware drops its key and re-runs
            # setup (which only succeeds inside a pairing window). Never a full reset.
            return _json({"status": 500, "message": "Unknown device, re-running setup"})

        screen.telemetry = {h: request.headers[h] for h in TELEMETRY_HEADERS
                            if h in request.headers}
        now = time.time()
        if request.headers.get("Update-Source") in BUTTON_SOURCES:
            # B-089: render before answering, so this very wake shows the new layout.
            renderer = hub.renderers.get(screen.subentry_id)
            if renderer is not None:
                if request.headers.get("special_function"):
                    await renderer.async_resume()  # double click: back to the schedule
                else:
                    await renderer.async_step()  # short press: next layout
        rate = 60 if screen.frame is None else _refresh_rate(self.hass, hub, screen)
        screen.last_checkin, screen.last_rate = now, rate
        hub.devices.record_checkin(screen.subentry_id, now, rate)
        async_dispatcher_send(self.hass, SIGNAL_CHECKIN.format(screen.subentry_id))
        if screen.frame is None:
            return _json({"status": 202, "message": "No image rendered yet",
                          "refresh_rate": rate})
        return _json({"status": 0,
                      "image_url": base_url(hub, request) + image_path(screen),
                      "filename": screen.frame.sha,
                      "refresh_rate": rate,
                      "update_firmware": False, "reset_firmware": False,
                      "special_function": "none"})


MAX_LOG_BODY = 64 * 1024
LOG_FIELDS = ("created_at", "message", "level", "source_path", "source_line", "wifi_signal",
              "battery_voltage", "firmware_version", "wake_reason", "special_function",
              "free_heap_size", "refresh_rate", "sleep_duration", "retry")


class LogView(HomeAssistantView):
    """POST /api/log: keep the device's recent log lines for diagnostics."""

    url = "/api/log"
    name = "api:paperboard:log"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        screen = _authenticated_screen(_hub(self.hass), request)
        if screen is None:
            return web.Response(status=HTTPStatus.FORBIDDEN)
        if (request.content_length or 0) > MAX_LOG_BODY:
            return web.Response(status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        try:
            payload = json.loads(await request.read())
            entries = payload.get("logs", []) if isinstance(payload, dict) else []
        except ValueError:
            return web.Response(status=HTTPStatus.BAD_REQUEST)
        for entry in entries[:50]:
            if isinstance(entry, dict):
                screen.logs.append({k: entry[k] for k in LOG_FIELDS if k in entry})
        return web.Response(status=HTTPStatus.NO_CONTENT)
