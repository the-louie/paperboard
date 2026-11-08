"""Paired-device secrets, kept in HA's .storage rather than in the config entry.

Writing them into the screen subentry would fire the update listener and reload the hub in
the middle of pairing (the device fetches its first image right after /api/setup).
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import asdict, dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1


@dataclass
class PairedDevice:
    mac: str
    api_key: str
    friendly_id: str


def friendly_id(mac: str) -> str:
    """Same scheme as the owner's trmnl-service, so the panel shows a familiar code."""
    return hashlib.sha256(mac.upper().encode()).hexdigest()[:6].upper()


def new_device(mac: str) -> PairedDevice:
    return PairedDevice(mac=mac.upper(), api_key=secrets.token_urlsafe(32),
                        friendly_id=friendly_id(mac))


class DeviceStore:
    """screen subentry_id -> PairedDevice, persisted with a debounce."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, dict[str, str]]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.devices")
        self.devices: dict[str, PairedDevice] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.devices = {sid: PairedDevice(**d) for sid, d in data.items()}

    def bind(self, screen_id: str, device: PairedDevice) -> None:
        # One MAC belongs to one screen: re-pairing elsewhere unbinds it here.
        for sid in [s for s, d in self.devices.items() if d.mac == device.mac]:
            del self.devices[sid]
        self.devices[screen_id] = device
        self._store.async_delay_save(self._data, 1)

    def forget(self, screen_id: str) -> None:
        if self.devices.pop(screen_id, None):
            self._store.async_delay_save(self._data, 1)

    def screen_for_mac(self, mac: str) -> str | None:
        return next((sid for sid, d in self.devices.items() if d.mac == mac.upper()), None)

    def _data(self) -> dict[str, dict[str, str]]:
        return {sid: asdict(d) for sid, d in self.devices.items()}
