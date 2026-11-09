"""Almanac widgets (mockup 07): big date block and a week of weather + events per day."""

from __future__ import annotations

import datetime as dt

from . import fmt, i18n
from .icons import weather_icon
from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import Rect
from .widgets_agenda import _start
from .widgets_weather import _when


def date_block(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
               flag: str = "") -> bool:
    """Day-of-month as a giant numeral with weekday, month/year, week and today's flag."""
    lang = snap.lang
    p = theme.px
    big = theme.numeral("hero")
    day = str(snap.now.day)
    svg.text(r.x - p(3), r.y + r.h / 2 + big.size * 0.36, day, big)
    x = r.x + measure.width(day, big) + p(10)
    lines = [(i18n.tl(lang, "date.weekday")[snap.now.weekday()], theme.text("m", bold=True)),
             (f"{i18n.tl(lang, 'date.month')[snap.now.month - 1]} {snap.now.year}",
              theme.text("s")),
             (f"{i18n.t(lang, 'date.week')} {snap.now.isocalendar().week}",
              theme.text("s"))]
    if flag:
        lines.append((flag, theme.text("s", bold=True)))
    y = r.y + r.h / 2 - len(lines) * p(9) + p(12)
    for text, style in lines:
        svg.text(x, y, measure.truncate(text, style, r.x + r.w - x), style)
        y += p(19)
    return True


def _events_by_day(snap: Snapshot) -> dict[dt.date, list[tuple[str, str]]]:
    out: dict[dt.date, list[tuple[str, str]]] = {}
    tz = snap.now.tzinfo
    for cal in [c for c in (snap.roles.get("calendars") or []) if isinstance(c, str)]:
        for ev in snap.events.get(cal, []):
            if not isinstance(ev, dict) or (start := _start(ev, tz)) is None:
                continue
            summary = str(ev.get("summary", ""))
            summary = i18n.holiday(snap.lang, summary)
            out.setdefault(start.date(), []).append(
                ("" if ev.get("all_day") else f"{start:%H:%M}", summary))
    for items in out.values():
        items.sort(key=lambda i: (i[0] != "", i[0]))
    return out


def week(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
         days: int = 6) -> bool:
    """One column per day: name + date (today inverted), weather, then that day's events."""
    forecast = {w.date(): i for i in snap.forecasts.get("daily", [])
                if (w := _when(i, snap)) is not None}
    events = _events_by_day(snap)
    if not forecast and not events:
        return False
    cw = r.w / days
    lang = snap.lang
    p = theme.px
    head, small, body = theme.text("s", bold=True), theme.text("xs"), theme.text("xs")
    for i in range(days):
        day = snap.now.date() + dt.timedelta(days=i)
        x = r.x + i * cw
        if i:
            svg.line(x, r.y, x, r.y + r.h, 1)
        ink = theme.ink
        if i == 0:
            svg.rect(x, r.y, cw, p(22), theme.ink)
            ink = theme.paper
        name = i18n.t(lang, "date.today") if i == 0 else \
            i18n.tl(lang, "date.weekday_abbr")[day.weekday()]
        svg.text(x + p(6), r.y + p(16), name.upper(), head, color=ink)
        svg.text(x + cw - p(6), r.y + p(16), str(day.day), theme.text("m", bold=True), "end",
                 ink)
        y = r.y + p(30)
        if (item := forecast.get(day)) is not None:
            weather_icon(svg, item.get("condition"), x + p(6), y, p(24))
            svg.text(x + p(36), y + p(13), fmt.with_unit(item.get("temperature"), "°", 0, lang),
                     theme.text("s", bold=True))
            svg.text(x + p(36), y + p(26), fmt.with_unit(item.get("templow"), "°", 0, lang),
                     small)
            rain = fmt.to_float(item.get("precipitation"))
            svg.text(x + p(6), y + p(42), f"{fmt.number(rain, 1, lang)} mm" if rain else
                     i18n.t(lang, "weather.dry_day"), small)
            y += p(50)
        svg.line(x + p(4), y, x + cw - p(4), y, 1, dash="1 2")
        y += p(4)
        for when, summary in events.get(day, []):
            if y + p(26) > r.y + r.h:
                break
            if when:
                svg.text(x + p(6), y + p(11), when, theme.text("xs", bold=True))
                y += p(12)
            svg.text(x + p(6), y + p(12), measure.truncate(summary, body, cw - p(10)), body)
            y += p(16)
    return True
