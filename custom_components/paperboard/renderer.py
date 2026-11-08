"""Render scheduling: snapshot in the event loop, draw in the executor, never on a request.

Triggers: state changes of the layout's entities (debounced), a 60 s tick that only renders
when the snapshot hash changed (time is part of the hash at the layout's clock resolution),
and an initial render at setup. A failed render keeps the previous frame, flagged stale.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import time
from typing import Any

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import SIGNAL_FRAME
from .fmt import to_float
from .fonts import FontRegistry
from .layouts import Layout, Snapshot
from .pipeline import PanelProfile, PipelineError, render
from .prices import PriceSnapshot
from .role_watch import bound_entities
from .runtime import ScreenRuntime, battery_percent
from .text import Measurer
from .widgets_sky import sun_times

_LOGGER = logging.getLogger(__name__)
TICK = dt.timedelta(seconds=60)
SLOW_RENDER_MS = 500  # budget per frame (T-29); slower renders are logged once
DEBOUNCE_SECONDS = 5.0


class ScreenRenderer:
    """Keeps one screen's frame current."""

    def __init__(self, hass: HomeAssistant, screen: ScreenRuntime, layout: Layout,
                 profile: PanelProfile, fonts: FontRegistry, hub: Any = None) -> None:
        self.hass, self.screen, self.layout, self.profile = hass, screen, layout, profile
        self.fonts = fonts
        self._measurer = Measurer(fonts)
        self._last_hash: str | None = None
        self.renders = 0  # completed renders, for diagnostics and tests
        self.last_render_ms: float | None = None
        self.max_render_ms = 0.0
        self._warned_slow = False
        self._debouncer = Debouncer(hass, _LOGGER, cooldown=DEBOUNCE_SECONDS, immediate=False,
                                    function=self.async_render)
        self._unsubs: list[Any] = []
        self.hub = hub
        roles = hub.roles if hub is not None else {}
        bound = [eid for _role, eid in bound_entities(roles)]
        self.entities = tuple(dict.fromkeys((*layout.resolve(hass.states.async_entity_ids()),
                                             *bound)))

    @callback
    def async_start(self) -> None:
        if self.entities:
            self._unsubs.append(async_track_state_change_event(
                self.hass, list(self.entities), self._state_changed))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, TICK))
        self.hass.async_create_background_task(self.async_render(), "paperboard initial render")

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._debouncer.async_cancel()

    @callback
    def _state_changed(self, event: Event[EventStateChangedData]) -> None:
        self.hass.async_create_task(self._debouncer.async_call())

    async def _tick(self, _now: dt.datetime) -> None:
        await self.async_render()

    def snapshot(self) -> Snapshot:
        """Collected in the event loop: only plain data crosses into the executor."""
        states: dict[str, dict[str, Any]] = {}
        for entity_id in self.entities:
            if (st := self.hass.states.get(entity_id)) is not None:
                states[entity_id] = {"state": st.state, "attributes": dict(st.attributes),
                                     "last_changed": st.last_changed.isoformat()}
        stale = None
        if self.screen.stale and self.screen.frame_time is not None:
            stale = dt_util.as_local(self.screen.frame_time).strftime("%H:%M")
        volts = to_float(self.screen.telemetry.get("Battery-Voltage"))
        return Snapshot(now=dt_util.now(), width=self.profile.width, height=self.profile.height,
                        screen_name=self.screen.name, states=states, stale_since=stale,
                        battery=battery_percent(volts) if volts is not None else None,
                        lang="sv" if self.hass.config.language.startswith("sv") else "en",
                        roles=dict(self.hub.roles) if self.hub is not None else {},
                        forecasts={k: list(v) for k, v in self.hub.forecasts.forecasts.items()}
                        if self.hub is not None and self.hub.forecasts is not None else {},
                        prices=PriceSnapshot.of(self.hub.prices.series())
                        if self.hub is not None and self.hub.prices is not None else None,
                        solar=self.hub.solar.snapshot()
                        if self.hub is not None and self.hub.solar is not None else None,
                        sun=sun_times(self.hass, dt_util.now().date()))

    def _hash(self, snap: Snapshot) -> str:
        bucket = int(snap.now.timestamp()) // self.layout.clock_resolution
        blob = json.dumps([bucket, snap.screen_name, snap.states, snap.stale_since,
                           snap.battery, snap.forecasts,
                           snap.prices.points if snap.prices else None,
                           (snap.solar.hours, snap.solar.today_kwh) if snap.solar else None],
                          sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    async def async_render(self) -> None:
        snap = self.snapshot()
        digest = self._hash(snap)
        if digest == self._last_hash and self.screen.frame is not None:
            return
        started = time.perf_counter()
        try:
            frame = await self.hass.async_add_executor_job(self._draw, snap)
        except PipelineError as err:
            self.screen.render_failed(str(err))
            async_dispatcher_send(self.hass, SIGNAL_FRAME.format(self.screen.subentry_id))
            _LOGGER.warning("Render of %s failed, keeping the last image: %s",
                            self.screen.name, err)
            return
        except Exception as err:  # a layout bug must not take the screen down
            self.screen.render_failed(f"{type(err).__name__}: {err}")
            async_dispatcher_send(self.hass, SIGNAL_FRAME.format(self.screen.subentry_id))
            _LOGGER.exception("Layout error on %s, keeping the last image", self.screen.name)
            return
        self._last_hash = digest
        self.renders += 1
        self.last_render_ms = (time.perf_counter() - started) * 1000
        self.max_render_ms = max(self.max_render_ms, self.last_render_ms)
        if self.last_render_ms > SLOW_RENDER_MS and not self._warned_slow:
            self._warned_slow = True
            _LOGGER.warning("Rendering %s took %.0f ms (budget %d ms)", self.screen.name,
                            self.last_render_ms, SLOW_RENDER_MS)
        had_error = self.screen.last_error is not None
        if self.screen.set_frame(frame) or had_error:
            async_dispatcher_send(self.hass, SIGNAL_FRAME.format(self.screen.subentry_id))

    def _draw(self, snap: Snapshot):  # runs in the executor
        return render(self.layout.build(snap, self._measurer), self.profile,
                      self.fonts.font_dir)
