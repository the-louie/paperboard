"""Base entity tied to one screen's device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .runtime import HubRuntime, ScreenRuntime


class ScreenEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: HubRuntime, screen: ScreenRuntime, key: str) -> None:
        self.hub, self.screen = hub, screen
        self._attr_unique_id = f"{screen.subentry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, screen.subentry_id)})
