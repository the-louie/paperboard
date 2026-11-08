"""Pair button: opens a 5-minute pairing window for its screen."""

from __future__ import annotations

import secrets

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PaperboardConfigEntry
from .const import CONF_IMAGE_TOKEN
from .entity import ScreenEntity


async def async_setup_entry(hass: HomeAssistant, entry: PaperboardConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    for screen in hub.screens.values():
        async_add_entities([PairButton(hub, screen, "pair"),
                            RotateTokenButton(hub, screen, "rotate_token")],
                           config_subentry_id=screen.subentry_id)


class PairButton(ScreenEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:link-variant"

    async def async_press(self) -> None:
        self.hub.open_pairing(self.screen.subentry_id)


class RotateTokenButton(ScreenEntity, ButtonEntity):
    """Mint a new image-URL token: a leaked link (proxy log, screenshot) stops working.

    The device itself is unaffected; it learns the new URL on its next check-in. Writing the
    subentry reloads the hub, which re-renders immediately.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:key-change"

    async def async_press(self) -> None:
        entry = self.platform.config_entry
        subentry = entry.subentries[self.screen.subentry_id]
        self.hass.config_entries.async_update_subentry(
            entry, subentry,
            data={**subentry.data, CONF_IMAGE_TOKEN: secrets.token_urlsafe(32)})
