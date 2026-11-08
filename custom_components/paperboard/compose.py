"""YAML layout -> rendered SVG: grid areas, widget registry, collapse/reflow, shared axes.

Every widget call is isolated: an exception inside one widget is logged into the snapshot's
render notes and treated as 'empty' (the area collapses), so one broken section can never
blank the screen. Widgets in the same area share it top-to-bottom in list order.
"""

from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Callable
from typing import Any

from .grid import Grid
from .layout_file import LayoutSpec
from .layouts import Layout, Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .timeaxis import TimeAxis
from .widgets import Rect

_LOGGER = logging.getLogger(__name__)
WidgetFn = Callable[[Svg, Rect, Snapshot, Measurer, Theme, dict[str, Any]], bool]
REGISTRY: dict[str, WidgetFn] = {}


def widget(name: str) -> Callable[[WidgetFn], WidgetFn]:
    def register(fn: WidgetFn) -> WidgetFn:
        REGISTRY[name] = fn
        return fn
    return register


def _inner(r: Rect, padding: list[int]) -> Rect:
    pv, ph = padding
    return Rect(r.x + ph, r.y + pv, max(0.0, r.w - 2 * ph), max(0.0, r.h - 2 * pv))


def _draw(fn: WidgetFn, rect: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
          options: dict[str, Any], notes: list[str], name: str) -> str | None:
    """Draw into a scratch Svg; return its fragment, or None if empty/failed."""
    scratch = Svg(snap.width, snap.height)
    try:
        ok = fn(scratch, rect, snap, measure, theme, options)
    except Exception as err:  # one broken widget must not blank the screen
        _LOGGER.debug("Widget %s failed", name, exc_info=True)
        notes.append(f"{name}: {type(err).__name__}: {err}")
        return None
    return scratch.fragment() if ok else None


def render_spec(spec: LayoutSpec, snap: Snapshot, measure: Measurer, theme: Theme,
                notes: list[str] | None = None) -> str:
    notes = notes if notes is not None else []
    g = spec.grid
    grid = Grid.build(g["columns"], g["rows"], g["areas"], snap.width, snap.height)
    padding = g.get("padding", [8, 16])
    by_area: dict[str, list[dict[str, Any]]] = {}
    for w in spec.widgets:
        by_area.setdefault(w["area"], []).append(w)

    # Pass 1: find empty areas (all widgets in it empty) and collapse them into neighbours.
    empty: list[str] = []
    for area in grid.names():
        widgets = by_area.get(area, [])
        rect = _inner(grid.rect(area), padding)
        if not widgets or all(
            _draw(REGISTRY[w["type"]], rect, snap, measure, theme, w["options"], notes,
                  w["type"]) is None for w in widgets if w["type"] in REGISTRY):
            empty.append(area)
    absorbed: dict[str, list[dict[str, Any]]] = {}
    for area in empty:
        collapse = next((w.get("collapse") for w in by_area.get(area, []) if w.get("collapse")),
                        None)
        if (taker := grid.collapse(area, collapse)) is not None:
            absorbed.setdefault(taker, [])
        by_area.pop(area, None)

    # Pass 2: draw every remaining area into its (possibly grown) rectangle.
    svg = Svg(snap.width, snap.height)
    for area in grid.names():
        widgets = [w for w in by_area.get(area, []) if w["type"] in REGISTRY]
        if not widgets:
            continue
        rect = _inner(grid.rect(area), padding)
        share = rect.h / len(widgets)
        for i, w in enumerate(widgets):
            sub = Rect(rect.x, rect.y + i * share, rect.w, share) if len(widgets) > 1 else rect
            frag = _draw(REGISTRY[w["type"]], sub, snap, measure, theme, w["options"], notes,
                         w["type"])
            if frag:
                svg.raw(frag)
                svg.adopt_patterns(frag)
    if g.get("rules", 2):
        for x1, y1, x2, y2 in grid.rules():
            svg.line(x1, y1, x2, y2, g["rules"])
    return str(svg)


def as_layout(spec: LayoutSpec, theme_for: Callable[[], Theme] | None = None) -> Layout:
    """Wrap a spec as a renderer Layout (entities come from the hub's roles)."""

    def build(snap: Snapshot, measure: Measurer) -> str:
        theme = theme_for() if theme_for else Theme()
        return render_spec(spec, snap, measure, theme)

    return Layout(build=build, clock_resolution=spec.clock_resolution)


def axis_for(snap: Snapshot, r: Rect, hours: int, gutter: float = 42) -> TimeAxis:
    return TimeAxis.from_now(snap.now, hours, r.x + gutter, r.x + r.w)


_ = dt  # re-exported for widget modules
