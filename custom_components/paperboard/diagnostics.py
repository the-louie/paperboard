"""Config-entry diagnostics: everything needed to debug a screen, no secrets."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import PaperboardConfigEntry
from .const import CONF_API_KEY, CONF_IMAGE_TOKEN

TO_REDACT = {CONF_API_KEY, CONF_IMAGE_TOKEN, "mac"}


def _mac_hint(mac: str | None) -> str | None:
    """Last two octets only: enough to tell devices apart, not to impersonate one."""
    return f"**:**:**:**:{mac[-5:]}" if mac and len(mac) >= 5 else mac


async def async_get_config_entry_diagnostics(hass: HomeAssistant,
                                              entry: PaperboardConfigEntry) -> dict[str, Any]:
    hub = entry.runtime_data
    screens: dict[str, Any] = {}
    for sid, screen in hub.screens.items():
        renderer = hub.renderers.get(sid)
        device = hub.devices.devices.get(sid)
        screens[sid] = {
            "name": screen.name,
            "config": async_redact_data(dict(entry.subentries[sid].data), TO_REDACT),
            "paired_device": _mac_hint(device.mac) if device else None,
            "friendly_id": device.friendly_id if device else None,
            "frame": {"sha": screen.frame.sha, "bytes": len(screen.frame.png),
                      "rendered": screen.frame_time.isoformat() if screen.frame_time else None}
                     if screen.frame else None,
            "stale": screen.stale,
            "last_error": screen.last_error,
            "renders": renderer.renders if renderer else None,
            "render_ms": {"last": round(renderer.last_render_ms or 0, 1),
                          "max": round(renderer.max_render_ms, 1)} if renderer else None,
            "entities": list(renderer.entities) if renderer else [],
            "refresh_rate": screen.refresh_rate,
            "last_checkin": dt_util.utc_from_timestamp(screen.last_checkin).isoformat()
            if screen.last_checkin else None,
            "telemetry": dict(screen.telemetry),
            "device_logs": list(screen.logs),
        }
    rejected = dict(hub.last_rejected) if hub.last_rejected else None
    if rejected:
        rejected["mac"] = _mac_hint(rejected.get("mac"))
    return {"options": dict(entry.options), "screens": screens,
            "pairing_open": hub.pairing_target() is not None, "last_rejected": rejected}
