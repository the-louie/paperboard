"""Time-series widgets that share one TimeAxis: price bars, expected solar, night shading.

Owner rules (vault, 2026-11-08): series that share time share one x-axis, stacked; prices as
hourly bars, the cheapest window filled and the rest outlined (from mockup 04), a bracket over
the cheapest window; figures never on lines.
"""

from __future__ import annotations

import datetime as dt

from . import fmt
from .layouts import Snapshot
from .prices import PriceSeries
from .style import Theme
from .svg import Svg
from .text import Measurer
from .timeaxis import TimeAxis
from .widgets import Rect

TOMORROW_NOTE = {"sv": ("morgondagens pris", "kommer ~{at}"),
                 "en": ("tomorrow's prices", "due ~{at}")}


def _label(svg: Svg, r: Rect, title: str, unit: str, theme: Theme) -> None:
    """Series label in the left gutter: bold title, unit below."""
    svg.text(r.x, r.y + 12, title, theme.text("xs", bold=True))
    if unit:
        svg.text(r.x, r.y + 25, unit, theme.text("xs"))


def price_chart(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
                axis: TimeAxis, cheapest_hours: int = 2, label: str = "EL") -> bool:
    series: PriceSeries = snap.prices.series() if snap.prices else PriceSeries()
    hourly = [p for p in series.hourly() if axis.contains(p.start)]
    if not hourly:
        return False
    currency = series.unit.split("/")[0] if series.unit else ""
    unit = {"SEK": "kr", "NOK": "kr", "DKK": "kr", "EUR": "€"}.get(currency, currency.lower())
    _label(svg, r, label, unit, theme)
    top, bottom = r.y + 16, r.y + r.h
    vmin, vmax = min(p.value for p in hourly), max(p.value for p in hourly)
    # Baseline below the minimum (not at zero) so the day's variation is readable; bars
    # still never touch the floor, so the cheapest hours keep a visible height.
    lo = max(0.0, vmin - (vmax - vmin) * 0.6) if vmin >= 0 else vmin * 1.1
    hi = vmax + (vmax - lo) * 0.08 or 1
    scale = (bottom - top) / (hi - lo)

    def y(v: float) -> float:
        return bottom - (v - lo) * scale

    best = series.cheapest_window(cheapest_hours, axis.start) if cheapest_hours else None
    cheap = set()
    if best:
        cheap = {best[0] + dt.timedelta(hours=i) for i in range(cheapest_hours)}
    for p in hourly:
        x0, x1 = axis.x(p.start), axis.x(p.end)
        if p.start in cheap:
            svg.rect(x0 + 1, y(p.value), x1 - x0 - 2, bottom - y(p.value), theme.ink)
        else:
            svg.rect(x0 + 2, y(p.value) + 1, x1 - x0 - 4, bottom - y(p.value) - 1, theme.paper,
                     stroke=theme.ink, stroke_width=1.5)
    if best:
        bx0, bx1 = axis.x(best[0]), axis.x(best[0] + dt.timedelta(hours=cheapest_hours))
        by = min(y(p.value) for p in hourly if p.start in cheap) - 8
        svg.path(f"M{bx0 + 1:.1f},{by + 5:.1f}V{by:.1f}H{bx1 - 1:.1f}V{by + 5:.1f}", width=2)
        text = f"{best[0]:%H}–{(best[0] + dt.timedelta(hours=cheapest_hours)):%H} " \
               f"{fmt.number(best[1], 2, snap.lang)}"
        tw = measure.width(text, theme.text("xs", bold=True))
        svg.rect((bx0 + bx1) / 2 - tw / 2 - 2, by - 15, tw + 4, 13, theme.paper)
        svg.text((bx0 + bx1) / 2, by - 4, text, theme.text("xs", bold=True), "middle")
    last_end = max(p.end for p in hourly)
    line1, line2 = TOMORROW_NOTE.get(snap.lang, TOMORROW_NOTE["en"])
    w = max(measure.width(line1, theme.text("xs")),
            measure.width(line2.format(at=series.tomorrow_expected_at or ""), theme.text("xs")))
    free = axis.x1 - axis.x(last_end)
    if last_end < axis.end and series.tomorrow_expected_at and free >= w + 10:
        nx = axis.x1 - 2
        svg.rect(nx - w - 4, top - 2, w + 6, 30, theme.paper)
        svg.text(nx, top + 10, line1, theme.text("xs"), "end")
        svg.text(nx, top + 24, line2.format(at=series.tomorrow_expected_at), theme.text("xs"),
                 "end")
    svg.line(axis.x0, bottom, axis.x1, bottom, 2)
    return True


def axis_labels(svg: Svg, axis: TimeAxis, y: float, theme: Theme, lang: str,
                every: int = 3) -> None:
    """Hour ticks under the stack; the first one reads 'nu'/'now'."""
    for x, t in axis.ticks(every):
        svg.line(x, y, x, y + 5, 2)
        first = t == axis.start
        svg.text(x, y + 18, ("nu" if lang == "sv" else "now") if first else f"{t:%H}",
                 theme.text("xs", bold=first), "middle")


def now_marker(svg: Svg, axis: TimeAxis, y0: float, y1: float) -> None:
    svg.line(axis.x0 + 1, y0, axis.x0 + 1, y1, 2, dash="3 3")


SOLAR_CAPTION = {"sv": "förväntat idag {total}", "en": "expected today {total}"}
SOLAR_LEFT = {"sv": " · kvar {left}", "en": " · {left} to go"}


def solar_chart(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
                axis: TimeAxis, label: str = "SOL") -> bool:
    """Expected production per hour as hatched bars (an estimate, not a measurement)."""
    hours = snap.solar.wh_at() if snap.solar else {}
    shown = {t: wh for t, wh in hours.items() if axis.contains(t) and wh > 0}
    if not shown:
        return False
    _label(svg, r, label, "kWh", theme)
    top, bottom = r.y + 18, r.y + r.h
    peak = max(max(shown.values()), 200.0)  # flat days do not blow up to full height
    for t, wh in shown.items():
        x0, x1 = axis.x(t), axis.x(t + dt.timedelta(hours=1))
        h = (bottom - top) * wh / peak
        svg.rect(x0 + 1, bottom - h, x1 - x0 - 2, h, theme.estimate, stroke=theme.ink,
                 stroke_width=1)
    total = snap.solar.today_kwh if snap.solar else None
    if total is not None:
        caption = SOLAR_CAPTION.get(snap.lang, SOLAR_CAPTION["en"]).format(
            total=fmt.with_unit(total, "kWh", 1, snap.lang))
        today = snap.now.date()
        left_wh = sum(wh for t, wh in hours.items() if t >= snap.now and t.astimezone(
            snap.now.tzinfo).date() == today)
        if hours:
            caption += SOLAR_LEFT.get(snap.lang, SOLAR_LEFT["en"]).format(
                left=fmt.number(left_wh / 1000, 1, snap.lang))
        style = theme.text("xs", bold=True)
        w = measure.width(caption, style)
        svg.rect(axis.x1 - w - 6, r.y, w + 6, 15, theme.paper)
        svg.text(axis.x1 - 2, r.y + 11, caption, style, "end")
    svg.line(axis.x0, bottom, axis.x1, bottom, 1)
    return True


def nights(snap: Snapshot) -> list[tuple[dt.datetime, dt.datetime]]:
    """Night intervals near now from the sun entity's next_setting/next_rising (UTC ISO)."""
    sun = snap.role_state("sun") or snap.states.get("sun.sun")
    attrs = (sun or {}).get("attributes", {})
    try:
        setting = dt.datetime.fromisoformat(str(attrs["next_setting"]))
        rising = dt.datetime.fromisoformat(str(attrs["next_rising"]))
    except (KeyError, ValueError):
        return []
    day = dt.timedelta(days=1)
    if setting < rising:  # daytime now
        return [(setting, rising), (setting + day, rising + day)]
    return [(snap.now - day, rising), (setting, rising + day)]  # night now


def night_shading(svg: Svg, snap: Snapshot, theme: Theme, axis: TimeAxis, top: float,
                  bottom: float, lang: str) -> None:
    """Dotted tint behind the stack where the sun is down, with set/rise times."""
    style = theme.text("xs")
    tz = snap.now.tzinfo
    for x0, x1 in axis.spans(nights(snap)):
        svg.rect(x0, top, x1 - x0, bottom - top, theme.tint)
    for a, b in nights(snap):
        if axis.contains(a):
            text = f"{'sol ned' if lang == 'sv' else 'sunset'} {a.astimezone(tz):%H:%M}"
            svg.rect(axis.x(a) + 1, top + 1, 74, 14, theme.paper)
            svg.text(axis.x(a) + 4, top + 12, text, style)
        if axis.contains(b):
            text = f"{'upp' if lang == 'sv' else 'sunrise'} {b.astimezone(tz):%H:%M}"
            svg.rect(axis.x(b) - 72, top + 1, 70, 14, theme.paper)
            svg.text(axis.x(b) - 3, top + 12, text, style, "end")
