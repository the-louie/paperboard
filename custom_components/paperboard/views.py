"""HTTP views. Device-facing views authenticate themselves (requires_auth=False) and always
*return* error responses - never raise HTTPUnauthorized - so HA's ip_ban is untouched (T-03).
Responses are built directly so they are never gzip-compressed (the firmware cannot inflate).
"""

from __future__ import annotations

import hmac
from http import HTTPStatus

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .runtime import HubRuntime, ScreenRuntime

IMAGE_URL = "/api/paperboard/image/{screen_id}/{token}/{filename}"


def image_path(screen: ScreenRuntime) -> str | None:
    if screen.frame is None:
        return None
    return f"/api/paperboard/image/{screen.subentry_id}/{screen.image_token}/{screen.frame.sha}.png"


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
        return web.Response(body=screen.frame.png, content_type="image/png", headers=headers)

    async def head(self, request: web.Request, screen_id: str, token: str,
                   filename: str) -> web.Response:
        """HA registers only the methods a view defines."""
        return await self.get(request, screen_id, token, filename)
