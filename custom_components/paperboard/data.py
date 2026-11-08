"""Service-backed data that is not in entity states: weather forecasts (and later prices).

Fetched in the event loop through HA services (never by importing integration internals),
cached, and copied into each render snapshot. Failures leave the cache empty or stale;
layouts render without the data. Never an exception toward a widget.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

_LOGGER = logging.getLogger(__name__)
REFRESH = dt.timedelta(minutes=30)
FORECAST_TYPES = ("hourly", "daily")


class ForecastCache:
    """weather.get_forecasts for one weather entity, both types, cached."""

    def __init__(self, hass: HomeAssistant, weather_entity: str | None) -> None:
        self.hass, self.entity = hass, weather_entity
        self.forecasts: dict[str, list[dict[str, Any]]] = {}
        self.fetched: dt.datetime | None = None
        self._debouncer = Debouncer(hass, _LOGGER, cooldown=10, immediate=True,
                                    function=self.async_refresh)

    async def async_refresh(self) -> None:
        if not self.entity:
            return
        for kind in FORECAST_TYPES:
            try:
                resp = await self.hass.services.async_call(
                    "weather", "get_forecasts", {"entity_id": self.entity, "type": kind},
                    blocking=True, return_response=True)
            except (HomeAssistantError, ValueError) as err:
                # Unsupported type, entity gone, service missing: no data of this kind.
                _LOGGER.debug("No %s forecast from %s: %s", kind, self.entity, err)
                self.forecasts.pop(kind, None)
                continue
            data = (resp or {}).get(self.entity, {})
            self.forecasts[kind] = list(data.get("forecast") or [])
        self.fetched = dt.datetime.now(dt.UTC)

    @callback
    def async_start(self) -> callback:
        if not self.entity:
            return lambda: None
        unsub_state = async_track_state_change_event(self.hass, [self.entity], self._changed)
        unsub_timer = async_track_time_interval(self.hass, self._tick, REFRESH)
        self.hass.async_create_background_task(self.async_refresh(), "paperboard forecasts")

        def _stop() -> None:
            unsub_state()
            unsub_timer()
            self._debouncer.async_cancel()
        return _stop

    @callback
    def _changed(self, _event: Event[EventStateChangedData]) -> None:
        self.hass.async_create_task(self._debouncer.async_call())

    async def _tick(self, _now: dt.datetime) -> None:
        await self.async_refresh()
