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
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .prices import PriceSeries, from_service, from_state

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


class PriceProvider:
    """The price role as a PriceSeries.

    Attribute-carrying sensors (HACS nordpool, ENTSO-e, ...) are parsed at snapshot time from
    the state. Core nordpool exposes no list on its entities, so its service is called for
    today and tomorrow and cached (refreshed every 30 min and on state changes).
    """

    def __init__(self, hass: HomeAssistant, entity_id: str | None) -> None:
        self.hass, self.entity = hass, entity_id
        self._service_series: PriceSeries | None = None
        self._core_entry: str | None = None
        if entity_id:
            entry = er.async_get(hass).async_get(entity_id)
            if entry is not None and entry.platform == "nordpool" and entry.config_entry_id:
                self._core_entry = entry.config_entry_id

    def series(self) -> PriceSeries:
        if self._core_entry:
            return self._service_series or PriceSeries()
        state = self.hass.states.get(self.entity) if self.entity else None
        if state is None:
            return PriceSeries()
        return from_state({"state": state.state, "attributes": dict(state.attributes)},
                          dt_util.now())

    async def async_refresh(self) -> None:
        if not self._core_entry:
            return
        today = dt_util.now().date()
        merged: dict[str, list[dict[str, Any]]] = {}
        currency = ""
        for day in (today, today + dt.timedelta(days=1)):
            try:
                resp = await self.hass.services.async_call(
                    "nordpool", "get_prices_for_date",
                    {"config_entry": self._core_entry, "date": day.isoformat(),
                     "resolution": 15}, blocking=True, return_response=True)
            except (HomeAssistantError, ValueError) as err:
                _LOGGER.debug("No Nord Pool prices for %s: %s", day, err)
                continue
            for area, rows in (resp or {}).items():
                merged.setdefault(area, []).extend(rows or [])
        entry = self.hass.config_entries.async_get_entry(self._core_entry)
        if entry is not None:
            currency = str(entry.data.get("currency", ""))
        area = next(iter(merged), None)
        self._service_series = from_service(merged, area, currency) if merged else None

    @callback
    def async_start(self) -> callback:
        if not self._core_entry:
            return lambda: None
        unsub = async_track_time_interval(self.hass, self._tick, REFRESH)
        self.hass.async_create_background_task(self.async_refresh(), "paperboard prices")
        return unsub

    async def _tick(self, _now: dt.datetime) -> None:
        await self.async_refresh()
