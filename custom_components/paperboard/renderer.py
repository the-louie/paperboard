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
from typing import Any

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import SIGNAL_FRAME
from .fonts import FontRegistry
from .layouts import Layout, Snapshot
from .pipeline import PanelProfile, PipelineError, render
from .runtime import ScreenRuntime
from .text import Measurer

_LOGGER = logging.getLogger(__name__)
TICK = dt.timedelta(seconds=60)
DEBOUNCE_SECONDS = 5.0


class ScreenRenderer:
    """Keeps one screen's frame current."""

    def __init__(self, hass: HomeAssistant, screen: ScreenRuntime, layout: Layout,
                 profile: PanelProfile, fonts: FontRegistry) -> None:
        self.hass, self.screen, self.layout, self.profile = hass, screen, layout, profile
        self.fonts = fonts
        self._measurer = Measurer(fonts)
        self._last_hash: str | None = None
        self.renders = 0  # completed renders, for diagnostics and tests
        self._debouncer = Debouncer(hass, _LOGGER, cooldown=DEBOUNCE_SECONDS, immediate=False,
                                    function=self.async_render)
        self._unsubs: list[Any] = []

    @callback
    def async_start(self) -> None:
        if self.layout.entities:
            self._unsubs.append(async_track_state_change_event(
                self.hass, list(self.layout.entities), self._state_changed))
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
        for entity_id in self.layout.entities:
            if (st := self.hass.states.get(entity_id)) is not None:
                states[entity_id] = {"state": st.state, "attributes": dict(st.attributes),
                                     "last_changed": st.last_changed.isoformat()}
        return Snapshot(now=dt_util.now(), width=self.profile.width, height=self.profile.height,
                        screen_name=self.screen.name, states=states)

    def _hash(self, snap: Snapshot) -> str:
        bucket = int(snap.now.timestamp()) // self.layout.clock_resolution
        blob = json.dumps([bucket, snap.screen_name, snap.states], sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    async def async_render(self) -> None:
        snap = self.snapshot()
        digest = self._hash(snap)
        if digest == self._last_hash and self.screen.frame is not None:
            return
        try:
            frame = await self.hass.async_add_executor_job(self._draw, snap)
        except PipelineError as err:
            self.screen.render_failed(str(err))
            _LOGGER.warning("Render of %s failed, keeping the last image: %s",
                            self.screen.name, err)
            return
        except Exception as err:  # a layout bug must not take the screen down
            self.screen.render_failed(f"{type(err).__name__}: {err}")
            _LOGGER.exception("Layout error on %s, keeping the last image", self.screen.name)
            return
        self._last_hash = digest
        self.renders += 1
        if self.screen.set_frame(frame):
            async_dispatcher_send(self.hass, SIGNAL_FRAME.format(self.screen.subentry_id))

    def _draw(self, snap: Snapshot):  # runs in the executor
        return render(self.layout.build(snap, self._measurer), self.profile,
                      self.fonts.font_dir)
