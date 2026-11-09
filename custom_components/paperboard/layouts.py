"""Layout builders: snapshot -> SVG. Pure functions, run in the executor.

Phase 2 replaces this registry with YAML grid layouts (B-028..B-030). Until then a builder is
a Python function, and an unknown layout name falls back to "status" - never an exception.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .fonts import PIXEL_SEMIBOLD
from .svg import Svg
from .text import Measurer, TextStyle


@dataclass(frozen=True)
class Snapshot:
    """Everything a layout may read: plain data, safe to hand to another thread."""

    now: dt.datetime
    width: int
    height: int
    screen_name: str
    states: dict[str, dict[str, Any]] = field(default_factory=dict)
    stale_since: str | None = None  # "HH:MM" of the frame still shown after a failed render
    battery: int | None = None  # the screen's own battery %, from its last check-in
    lang: str = "sv"
    roles: dict[str, Any] = field(default_factory=dict)  # role -> entity id / list of ids
    forecasts: dict[str, list[dict[str, Any]]] = field(default_factory=dict)  # hourly/daily
    prices: Any = None  # prices.PriceSnapshot or None
    solar: Any = None  # data.SolarSnapshot or None
    sun: dict[str, str] | None = None  # widgets_sky.sun_times() result
    events: dict[str, list[dict[str, Any]]] = field(default_factory=dict)  # calendar -> events
    texts: dict[str, str] = field(default_factory=dict)  # template source -> rendered text
    home_name: str = ""  # hass.config.location_name

    def role_state(self, role: str) -> dict[str, Any] | None:
        """State dict of the entity bound to a single role, or None."""
        entity_id = self.roles.get(role)
        return self.states.get(entity_id) if isinstance(entity_id, str) else None


@dataclass(frozen=True)
class Layout:
    build: Callable[[Snapshot, Measurer], str]
    entities: tuple[str, ...] = ()  # entity ids whose changes trigger a render
    clock_resolution: int = 300  # seconds; how often the visible clock may change the image
    # Optional: pick entities from all entity ids at start (zero-config layouts).
    discover: Callable[[list[str]], tuple[str, ...]] | None = None
    # HA Jinja templates used by text slots; rendered in the event loop per snapshot.
    templates: tuple[str, ...] = ()
    schedule: Any = None  # schedule.ScheduleSpec when this layout is a time-of-day schedule

    def resolve(self, entity_ids: list[str]) -> tuple[str, ...]:
        found = self.discover(entity_ids) if self.discover else ()
        return tuple(dict.fromkeys((*self.entities, *found)))


def build_status(snap: Snapshot, measure: Measurer) -> str:
    """Minimal screen: name and render time. Proves the pipeline end to end."""
    svg = Svg(snap.width, snap.height)
    svg.text(16, 40, snap.screen_name, TextStyle("TRMNL21", 700, 21))
    svg.text(16, snap.height - 12, f"{snap.now:%Y-%m-%d %H:%M}",
             TextStyle("TRMNL12", PIXEL_SEMIBOLD, 12))
    return str(svg)


def _first_weather(entity_ids: list[str]) -> tuple[str, ...]:
    weather = sorted(e for e in entity_ids if e.startswith("weather."))
    return tuple(weather[:1])


def build_now(snap: Snapshot, measure: Measurer) -> str:
    """Zero-config layout: outdoor now block and status footer (phase 1 demo)."""
    from .widgets import Rect, footer, now_block  # widgets imports Snapshot from here

    svg = Svg(snap.width, snap.height)
    if not now_block(svg, Rect(24, 24, 300, snap.height - 80), snap, measure, snap.lang):
        svg.text(24, 60, snap.screen_name, TextStyle("TRMNL21", 700, 21))
    footer(svg, Rect(16, snap.height - 26, snap.width - 32, 26), snap, measure, snap.lang,
           left=snap.screen_name)
    return str(svg)


LAYOUTS: dict[str, Layout] = {
    "status": Layout(build=build_status),
    "now": Layout(build=build_now, discover=_first_weather),
}


def get_layout(name: str) -> Layout:
    return LAYOUTS.get(name) or LAYOUTS["status"]
