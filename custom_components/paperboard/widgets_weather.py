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


def _when(item: Any, snap: Snapshot) -> dt.datetime | None:
    if not isinstance(item, dict):
        return None
    try:
        return dt.datetime.fromisoformat(str(item["datetime"])).astimezone(snap.now.tzinfo)
    except (KeyError, ValueError, TypeError):
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


HOURLY_HEAD = {"sv": {"time": "TID", "temp": "TEMP", "rain": "REGN", "wind": "VIND",
                      "price": "EL KR/KWH", "now": "Nu"},
               "en": {"time": "TIME", "temp": "TEMP", "rain": "RAIN", "wind": "WIND",
                      "price": "POWER /KWH", "now": "Now"}}


def hourly_table(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
                 hours: int = 10, row_h: float = 21.0) -> bool:
    """Departure-board table, one row per hour (mockup 05 Tavlan). The current hour's row is
    inverted. Columns without any data (no prices, no rain field) are dropped."""
    now_hour = snap.now.replace(minute=0, second=0, microsecond=0)
    items = [i for i in snap.forecasts.get("hourly", [])
             if (w := _when(i, snap)) is not None and w >= now_hour][:hours]
    if not items:
        return False
    unit = _weather_attrs(snap).get("wind_speed_unit")
    prices = {p.start: p.value for p in snap.prices.series().hourly()} if snap.prices else {}
    has_rain = any("precipitation" in i for i in items)
    has_price = any(_when(i, snap) in prices for i in items)
    head = HOURLY_HEAD.get(snap.lang, HOURLY_HEAD["en"])
    cols: list[tuple[str, float, str]] = [("time", 0.13, "start"), ("icon", 0.08, "middle"),
                                          ("temp", 0.13, "end")]
    if has_rain:
        cols.append(("rain", 0.13, "end"))
    cols.append(("wind", 0.18, "end"))
    if has_price:
        cols.append(("price", 0.35, "end"))
    total = sum(w for _, w, _ in cols)
    xs, x = [], r.x
    for _name, w, _a in cols:
        xs.append((x, x + r.w * w / total))
        x += r.w * w / total
    small, body, bold = theme.text("xs", bold=True), theme.text("s"), theme.text("s", bold=True)
    y = r.y + 12
    for (name, _w, anchor), (x0, x1) in zip(cols, xs, strict=True):
        if name != "icon":
            svg.text(x0 if anchor == "start" else x1 - 4, y, head[name], small, anchor)
    svg.line(r.x, y + 4, r.x + r.w, y + 4, 1)
    pmax = max(prices.values()) if prices else 1.0
    pmin = min(prices.values()) if prices else 0.0
    for n, item in enumerate(items):
        top = y + 6 + n * row_h
        if top + row_h > r.y + r.h:
            break
        when = _when(item, snap)
        current = when == now_hour
        ink = theme.paper if current else theme.ink
        if current:
            svg.rect(r.x, top, r.w, row_h, theme.ink)
        base = top + row_h - 5
        for (name, _w, anchor), (x0, x1) in zip(cols, xs, strict=True):
            tx = x0 if anchor == "start" else (x0 + x1) / 2 if anchor == "middle" else x1 - 4
            if name == "time":
                svg.text(tx, base, head["now"] if current else f"{when:%H}:00", bold,
                         anchor, ink)
            elif name == "icon":
                weather_icon(svg, item.get("condition"), tx - 9, top + 2, 18, ink)
            elif name == "temp":
                svg.text(tx, base, fmt.with_unit(item.get("temperature"), "°", 1, snap.lang),
                         bold, anchor, ink)
            elif name == "rain":
                rain = fmt.to_float(item.get("precipitation"))
                svg.text(tx, base, fmt.number(rain, 1, snap.lang) if rain else "–", body,
                         anchor, ink)
            elif name == "wind":
                svg.text(tx, base, fmt.with_unit(_ms(item.get("wind_speed"), unit), "m/s", 1,
                                                 snap.lang), body, anchor, ink)
            elif name == "price":
                value = prices.get(when)
                text = fmt.number(value, 2, snap.lang)
                svg.text(tx, base, text, bold, anchor, ink)
                if value is not None:
                    room = (x1 - x0) - measure.width("0,00", bold) - 14
                    bar = max(2.0, room * (value - pmin * 0.8) / (pmax - pmin * 0.8 or 1))
                    svg.rect(tx - measure.width(text, bold) - 6 - bar, top + 6, bar,
                             row_h - 12, ink)
        svg.line(r.x, top + row_h, r.x + r.w, top + row_h, 1)
    return True


def hourly_strip(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
                 hours: int = 12, title: str | None = None) -> bool:
    """Next N hours as columns: temperature, icon, hour - with a temperature line above."""
    now_hour = snap.now.replace(minute=0, second=0, microsecond=0)
    items = [i for i in snap.forecasts.get("hourly", [])
             if (w := _when(i, snap)) is not None and w >= now_hour][:hours]
    temps = [fmt.to_float(i.get("temperature")) for i in items]
    if not items:
        return False
    y = r.y
    if title:
        svg.text(r.x, y + 12, title, theme.text("xs", bold=True))
        y += 16
    cw = r.w / len(items)
    known = [t for t in temps if t is not None]
    if len(known) >= 2:
        lo, hi = min(known), max(known)
        span = (hi - lo) or 1
        pts = [(r.x + (i + 0.5) * cw, y + 4 + 18 * (1 - (t - lo) / span))
               for i, t in enumerate(temps) if t is not None]
        svg.path("M" + " L".join(f"{x:.1f},{yy:.1f}" for x, yy in pts), width=2.5)
        y += 26
    icon = 20 if r.h - (y - r.y) < 70 else 24
    for i, item in enumerate(items):
        cx = r.x + (i + 0.5) * cw
        svg.text(cx, y + 14, fmt.with_unit(temps[i], "°", 0, snap.lang),
                 theme.text("s", bold=True), "middle")
        weather_icon(svg, item.get("condition"), cx - icon / 2, y + 19, icon)
        svg.text(cx, y + 19 + icon + 13, f"{_when(item, snap):%H}", theme.text("xs"), "middle")
    return True


TOMORROW = {"sv": "IMORGON {hh}", "en": "TOMORROW {hh}"}


def tomorrow_at(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
                hour: int = 7) -> bool:
    """Tomorrow at HH from the hourly forecast: the 'what do the kids wear' number."""
    target = (snap.now + dt.timedelta(days=1)).replace(hour=hour, minute=0, second=0,
                                                       microsecond=0)
    item = next((i for i in snap.forecasts.get("hourly", []) if _when(i, snap) == target), None)
    if item is None:
        return False
    svg.text(r.x, r.y + 12, TOMORROW.get(snap.lang, TOMORROW["en"]).format(hh=f"{hour:02d}"),
             theme.text("xs", bold=True))
    big = theme.numeral("xl")
    svg.text(r.x - 2, r.y + 18 + big.size * 0.9,
             fmt.with_unit(item.get("temperature"), "°", 1, snap.lang), big)
    weather_icon(svg, item.get("condition"), r.x + r.w - 32, r.y + 18, 32)
    return True
