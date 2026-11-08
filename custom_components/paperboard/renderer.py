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
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .const import SIGNAL_CHECKIN, SIGNAL_FRAME
from .fmt import to_float
from .fonts import FontRegistry
from .layouts import Layout, Snapshot
from .pipeline import PanelProfile, PipelineError, render
from .prices import PriceSnapshot
from .profiles import resolve as resolve_profile
from .role_watch import bound_entities
from .runtime import ScreenRuntime, battery_percent
from .text import Measurer
from .widgets_sky import sun_times

_LOGGER = logging.getLogger(__name__)
TICK = dt.timedelta(seconds=60)
SLOW_RENDER_MS = 500  # budget per frame (T-29); slower renders are logged once
DEBOUNCE_SECONDS = 5.0
# Device button (B-089): a short press steps through these, each held for HOLD_MINUTES.
DEFAULT_CYCLE = ("tidslinjen", "tavlan", "almanackan", "energi", "tidningen", "bento", "trmnl")
HOLD_MINUTES = 30


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
        self.auto_profile = False  # set by setup: follow the device's reported model
        self.layout_name = ""
        self.hub = hub
        self.cycle: dict[str, Layout] = {}  # button cycle, name -> layout, in order
        self.hold = dt.timedelta(minutes=HOLD_MINUTES)
        self.held: tuple[str, dt.datetime] | None = None  # (layout name, until), button
        self._bound = [eid for _role, eid in bound_entities(hub.roles if hub else {})]
        self.entities = self._entities()

    def _entities(self) -> tuple[str, ...]:
        ids = self.hass.states.async_entity_ids()
        layouts = (self.layout, *self.cycle.values())
        return tuple(dict.fromkeys((*(e for lay in layouts for e in lay.resolve(ids)),
                                    *self._bound)))

    def set_cycle(self, cycle: dict[str, Layout], hold_minutes: int | None = None) -> None:
        """The layouts the device button steps through (before async_start)."""
        self.cycle = cycle
        self.hold = dt.timedelta(minutes=hold_minutes or HOLD_MINUTES)
        self.entities = self._entities()

    def held_layout(self, now: dt.datetime) -> tuple[str, Layout] | None:
        """The layout the button put up, while its hold lasts."""
        if self.held is None:
            return None
        name, until = self.held
        if now >= until or name not in self.cycle:
            self.held = None
            return None
        return name, self.cycle[name]

    def active_layout(self, now: dt.datetime) -> Layout:
        held = self.held_layout(now)
        return held[1] if held else self.layout

    def shown_name(self, now: dt.datetime) -> str:
        """The name of the layout on screen now (held, scheduled or fixed)."""
        if (held := self.held_layout(now)) is not None:
            return held[0]
        schedule = getattr(self.layout, "schedule", None)
        if schedule is not None:
            states = {e: {"state": s.state} for e in schedule.conditions
                      if (s := self.hass.states.get(e)) is not None}
            return schedule.layout_at(now, states)
        return self.layout_name

    async def async_step(self) -> None:
        """Button short press: the next layout in the cycle, held for the hold time."""
        names = list(self.cycle)
        if not names:
            return
        now = dt_util.now()
        current = self.shown_name(now)
        nxt = names[(names.index(current) + 1) % len(names)] if current in names else names[0]
        self.held = (nxt, now + self.hold)
        _LOGGER.debug("%s: button -> %s until %s", self.screen.name, nxt, self.held[1])
        await self.async_render()

    async def async_resume(self) -> None:
        """Button double click: back to the schedule now."""
        self.held = None
        await self.async_render()

    @callback
    def async_start(self) -> None:
        if self.entities:
            self._unsubs.append(async_track_state_change_event(
                self.hass, list(self.entities), self._state_changed))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, TICK))
        self._unsubs.append(async_dispatcher_connect(
            self.hass, SIGNAL_CHECKIN.format(self.screen.subentry_id), self._checkin))
        self.hass.async_create_background_task(self.async_render(), "paperboard initial render")

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._debouncer.async_cancel()

    @callback
    def _checkin(self) -> None:
        """With profile 'auto', adopt the panel the device says it is (first poll, swaps)."""
        if not self.auto_profile:
            return
        t = self.screen.telemetry
        prof = resolve_profile(t.get("Model"), to_int(t.get("Width")), to_int(t.get("Height")))
        wanted = PanelProfile(prof.width, prof.height, prof.bit_depth, prof.byte_limit)
        if wanted == self.profile:
            return
        self.profile = wanted
        if self.hub is not None and self.hub.layouts is not None:
            from . import layout_for  # late: __init__ imports this module

            self.layout = layout_for(self.hub.layouts, self.layout_name, prof.bit_depth)
            self.cycle = {n: layout_for(self.hub.layouts, n, prof.bit_depth) for n in self.cycle}
        self._last_hash = None
        self.hass.async_create_background_task(self.async_render(), "paperboard re-profile")

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
                        sun=sun_times(self.hass, dt_util.now().date()),
                        events={k: list(v) for k, v in self.hub.calendars.events.items()}
                        if self.hub is not None and self.hub.calendars is not None else {},
                        texts=self._render_templates(),
                        home_name=self.hass.config.location_name or "")

    def _render_templates(self) -> dict[str, str]:
        """HA Jinja for text slots, in the loop; a broken template shows its error briefly."""
        out = {}
        for source in self.active_layout(dt_util.now()).templates:
            try:
                out[source] = str(Template(source, self.hass).async_render(parse_result=False))
            except TemplateError as err:
                out[source] = f"⚠ {str(err)[:80]}"
        return out

    def _hash(self, snap: Snapshot) -> str:
        layout = self.active_layout(snap.now)
        bucket = int(snap.now.timestamp()) // layout.clock_resolution
        held = self.held[0] if self.held else None
        blob = json.dumps([bucket, held, snap.screen_name, snap.states, snap.stale_since,
                           snap.battery, snap.forecasts,
                           snap.prices.points if snap.prices else None,
                           (snap.solar.hours, snap.solar.today_kwh) if snap.solar else None,
                           snap.events, snap.texts],
                          sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    async def async_render(self) -> None:
        snap = self.snapshot()
        digest = self._hash(snap)
        if digest == self._last_hash and self.screen.frame is not None:
            return
        started = time.perf_counter()
        try:
            frame = await self.hass.async_add_executor_job(
                self._draw, snap, self.active_layout(snap.now))
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

    def _draw(self, snap: Snapshot, layout: Layout):  # runs in the executor
        return render(layout.build(snap, self._measurer), self.profile, self.fonts.font_dir)


def to_int(value: object) -> int | None:
    number = to_float(value)
    return int(number) if number is not None else None
