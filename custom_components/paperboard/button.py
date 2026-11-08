"""Pair button: opens a 5-minute pairing window for its screen."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PaperboardConfigEntry
from .entity import ScreenEntity


async def async_setup_entry(hass: HomeAssistant, entry: PaperboardConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    for screen in hub.screens.values():
        async_add_entities([PairButton(hub, screen, "pair")],
                           config_subentry_id=screen.subentry_id)


class PairButton(ScreenEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:link-variant"

    async def async_press(self) -> None:
        self.hub.open_pairing(self.screen.subentry_id)
