"""Missed check-in: a screen that stops polling is a problem, not silence (O4)."""

from __future__ import annotations

import datetime as dt
import time

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from . import PaperboardConfigEntry
from .const import SIGNAL_CHECKIN
from .entity import ScreenEntity
from .runtime import HubRuntime, ScreenRuntime

MISSED_POLLS = 3
CHECK_EVERY = dt.timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: PaperboardConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    for screen in hub.screens.values():
        async_add_entities([MissedCheckin(hub, screen, "missed_checkin")],
                           config_subentry_id=screen.subentry_id)


class MissedCheckin(ScreenEntity, BinarySensorEntity):
    """On when the device has not polled for MISSED_POLLS x the refresh rate it was last given.

    The last check-in and that rate survive restarts (B-093). The rate is the one in the last
    answer, not the screen's base rate: at night the schedule tells the device to sleep 1 h,
    and 3 x the 15 min base rate turned this on every night hour (seen 2026-11-08/09).
    Before any check-in the clock starts at setup, so a device that never shows up also
    turns this on.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, hub: HubRuntime, screen: ScreenRuntime, key: str) -> None:
        super().__init__(hub, screen, key)
        self._since = time.time()

    @property
    def _allowed(self) -> int:
        return MISSED_POLLS * (self.screen.last_rate or self.screen.refresh_rate)

    @property
    def is_on(self) -> bool:
        reference = self.screen.last_checkin or self._since
        return time.time() - reference > self._allowed

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"allowed_seconds": self._allowed}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, SIGNAL_CHECKIN.format(self.screen.subentry_id), self._update))
        self.async_on_remove(async_track_time_interval(self.hass, self._tick, CHECK_EVERY))

    @callback
    def _tick(self, _now: dt.datetime) -> None:
        self._update()

    @callback
    def _update(self) -> None:
        self.async_write_ha_state()
