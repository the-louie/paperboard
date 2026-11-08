"""One image entity per screen: the frame as served to the device (preview, history)."""

from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import PaperboardConfigEntry
from .const import SIGNAL_FRAME
from .entity import ScreenEntity
from .runtime import HubRuntime, ScreenRuntime


async def async_setup_entry(hass: HomeAssistant, entry: PaperboardConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    for screen in hub.screens.values():
        async_add_entities([ScreenImage(hass, hub, screen)],
                           config_subentry_id=screen.subentry_id)


class ScreenImage(ScreenEntity, ImageEntity):
    _attr_content_type = "image/png"

    def __init__(self, hass: HomeAssistant, hub: HubRuntime, screen: ScreenRuntime) -> None:
        ScreenEntity.__init__(self, hub, screen, "frame")
        ImageEntity.__init__(self, hass)
        if screen.frame is not None:
            self._attr_image_last_updated = dt_util.utcnow()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, SIGNAL_FRAME.format(self.screen.subentry_id), self._new_frame))

    @callback
    def _new_frame(self) -> None:
        self._attr_image_last_updated = dt_util.utcnow()
        self.async_write_ha_state()

    async def async_image(self) -> bytes | None:
        """Cheap: returns cached bytes (the render happens elsewhere, off the loop)."""
        return self.screen.frame.png if self.screen.frame else None
