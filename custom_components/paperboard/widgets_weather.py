"""Forecast widgets: daily columns with warning inversion, hourly table."""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import fmt
from .icons import weather_icon
from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import Rect, _ms

DAYS = {"sv": ["Mån", "Tis", "Ons", "Tor", "Fre", "Lör", "Sön"],
        "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
TODAY = {"sv": "Idag", "en": "Today"}


def _weather_attrs(snap: Snapshot) -> dict[str, Any]:
    st = snap.role_state("weather")
    if st is None:
        st = next((v for k, v in snap.states.items() if k.startswith("weather.")), None)
    return (st or {}).get("attributes", {})


def _when(item: dict[str, Any], snap: Snapshot) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(str(item["datetime"])).astimezone(snap.now.tzinfo)
    except (KeyError, ValueError):
        return None


def daily(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme, days: int = 6,
          warn_gust_ms: float = 14.0, warn_rain_mm: float = 10.0) -> bool:
    """Day columns: name, icon, max, min. Wind and rain appear only when a day crosses a
    threshold, and that day's cell is inverted (owner, vault row 02)."""
    items = [i for i in snap.forecasts.get("daily", []) if _when(i, snap)][:days]
    if not items:
        return False
    unit = _weather_attrs(snap).get("wind_speed_unit")
    cw = r.w / len(items)
    icon = min(48.0, cw * 0.6, r.h * 0.32)
    icon = 24.0 * max(1, round(icon / 24)) if icon >= 24 else icon
    for i, item in enumerate(items):
        x = r.x + i * cw
        when = _when(item, snap)
        gust = _ms(item.get("wind_gust_speed", item.get("wind_speed")), unit)
        rain = fmt.to_float(item.get("precipitation"))
        warn_wind = gust is not None and gust >= warn_gust_ms
        warn_rain = rain is not None and rain >= warn_rain_mm
        warn = warn_wind or warn_rain
        ink = theme.paper if warn else theme.ink
        if warn:
            svg.rect(x + 2, r.y + 2, cw - 4, r.h - 4, theme.ink, rx=4)
        elif i:
            svg.line(x, r.y + 4, x, r.y + r.h - 4, 1)
        name = TODAY[snap.lang] if when and when.date() == snap.now.date() else \
            DAYS[snap.lang][when.weekday()] if when else ""
        cx = x + cw / 2
        svg.text(cx, r.y + 18, name, theme.text("s", bold=True), "middle", ink)
        weather_icon(svg, item.get("condition"), cx - icon / 2, r.y + 26, icon, ink)
        ty = r.y + 26 + icon + 22
        svg.text(cx, ty, fmt.with_unit(item.get("temperature"), "°", 0, snap.lang),
                 theme.text("m", bold=True), "middle", ink)
        svg.text(cx, ty + 18, fmt.with_unit(item.get("templow"), "°", 0, snap.lang),
                 theme.text("s"), "middle", ink)
        notes = []
        if warn_rain:
            notes.append(f"{fmt.number(rain, 0, snap.lang)} mm")
        if warn_wind:
            notes.append(f"{fmt.number(gust, 0, snap.lang)} m/s")
        for j, note in enumerate(notes):
            svg.text(cx, ty + 36 + j * 15, note, theme.text("xs", bold=True), "middle", ink)
    return True
