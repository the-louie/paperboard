"""Layout builders: snapshot -> SVG. Pure functions, run in the executor.

Phase 2 replaces this registry with YAML grid layouts (B-028..B-030). Until then a builder is
a Python function, and an unknown layout name falls back to "status" - never an exception.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

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
    stale_since: str | None = None


@dataclass(frozen=True)
class Layout:
    build: Callable[[Snapshot, Measurer], str]
    entities: tuple[str, ...] = ()  # entity ids whose changes trigger a render
    clock_resolution: int = 300  # seconds; how often the visible clock may change the image


def build_status(snap: Snapshot, measure: Measurer) -> str:
    """Minimal screen: name and render time. Proves the pipeline end to end."""
    svg = Svg(snap.width, snap.height)
    svg.text(16, 40, snap.screen_name, TextStyle("TRMNL21", 700, 21))
    svg.text(16, snap.height - 12, f"{snap.now:%Y-%m-%d %H:%M}", TextStyle("TRMNL12", 400, 12))
    return str(svg)


LAYOUTS: dict[str, Layout] = {"status": Layout(build=build_status)}


def get_layout(name: str) -> Layout:
    return LAYOUTS.get(name) or LAYOUTS["status"]
