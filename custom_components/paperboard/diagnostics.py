"""Config-entry diagnostics: everything needed to debug a screen, no secrets."""

from __future__ import annotations

from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util.network import is_local

from . import PaperboardConfigEntry
from .const import CONF_API_KEY, CONF_BASE_URL, CONF_IMAGE_TOKEN

TO_REDACT = {CONF_API_KEY, CONF_IMAGE_TOKEN, CONF_BASE_URL, "mac"}
REDACTED = "**REDACTED**"


def _secrets(hub: Any) -> list[str]:
    """Every value that must never appear: image tokens, device keys, full MACs (in the
    spellings firmware log lines may use). Longest first, so no secret is half-replaced."""
    found = [s.image_token for s in hub.screens.values()]
    for d in hub.devices.devices.values():
        found += [d.api_key, d.mac, d.mac.lower(), d.mac.replace(":", ""),
                  d.mac.replace(":", "").lower()]
    return sorted({f for f in found if f and len(f) >= 6}, key=len, reverse=True)


def _scrub(value: Any, secrets: list[str]) -> Any:
    """Replace every known secret inside strings, recursively (free-text device logs, too)."""
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, REDACTED)
        return value
    if isinstance(value, dict):
        return {k: _scrub(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v, secrets) for v in value]
    return value


def _where(ip: str | None) -> str:
    """'local' or 'remote' instead of the address itself."""
    try:
        return "local" if is_local(ip_address(ip or "")) else "remote"
    except ValueError:
        return "?"


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
        rejected["ip"] = _where(rejected.get("ip"))
    base = entry.options.get(CONF_BASE_URL) or ""
    result = {"options": async_redact_data(dict(entry.options), TO_REDACT),
              "base_url": {"set": bool(base), "scheme": urlparse(base).scheme or None},
              "screens": screens,
              "pairing_open": hub.pairing_target() is not None, "last_rejected": rejected}
    # Safety net: the device's own log lines are free text and may quote the image URL.
    return _scrub(result, _secrets(hub))
