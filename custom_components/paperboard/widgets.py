"""Widgets: draw one block of a layout into a rectangle. Pure functions (executor-safe).

Contract (docs/research report, "Missing sensors never crash anything"): a widget never raises
on missing or garbage data; a missing value renders as an em dash; a widget with nothing at all
to show draws nothing and returns False, so the grid (phase 2) can collapse it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import fmt, i18n
from .layouts import Snapshot
from .style import Theme
from .svg import BLACK, Svg
from .text import Measurer


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float


def _weather(snap: Snapshot) -> tuple[str | None, dict[str, Any]]:
    for entity_id, st in snap.states.items():
        if entity_id.startswith("weather."):
            return st.get("state"), st.get("attributes", {})
    return None, {}


def _ms(value: object, unit: str | None) -> float | None:
    """Wind speed to m/s from HA's wind_speed_unit."""
    v = fmt.to_float(value)
    if v is None:
        return None
    return {"km/h": v / 3.6, "mph": v * 0.44704, "kn": v * 0.514444}.get(unit or "m/s", v)


def now_block(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, lang: str = "en",
              theme: Theme | None = None) -> bool:
    """Outdoor now: big temperature, condition, and a key/value list. Every field optional."""
    t = theme or Theme()
    p = t.px
    condition, attrs = _weather(snap)
    temp = attrs.get("temperature")
    rows = [
        (i18n.t(lang, "now.humidity"), fmt.with_unit(attrs.get("humidity"), "%", 0, lang)),
        (i18n.t(lang, "now.wind"), _wind(attrs, lang)),
        (i18n.t(lang, "now.dew"), fmt.with_unit(attrs.get("dew_point"), "°", 1, lang)),
        (i18n.t(lang, "now.pressure"), fmt.with_unit(attrs.get("pressure"), "hPa", 0, lang)),
    ]
    rows = [(k, v) for k, v in rows if v != fmt.MISSING]
    if fmt.to_float(temp) is None and condition is None and not rows:
        return False
    b12, r16, b16 = t.text("xs", bold=True), t.text("s"), t.text("s", bold=True)
    svg.text(r.x, r.y + p(12), i18n.t(lang, "now.now"), b12)
    svg.text(r.x - p(4), r.y + p(82), fmt.with_unit(temp, "°", 1, lang), t.numeral("hero"))
    label = i18n.group(lang, "weather.condition").get(condition or "", "")
    if label:
        svg.text(r.x, r.y + p(110), measure.truncate(label, r16, r.w), r16)
    y = r.y + p(140)
    for key, value in rows:
        if y > r.y + r.h - p(4):
            break
        svg.text(r.x, y, key, r16)
        svg.text(r.x + r.w, y, measure.truncate(value, b16, r.w * 0.6), b16, "end")
        y += p(21)
    return True


def _wind(attrs: dict[str, Any], lang: str) -> str:
    unit = attrs.get("wind_speed_unit")
    speed, gust = _ms(attrs.get("wind_speed"), unit), _ms(attrs.get("wind_gust_speed"), unit)
    if speed is None:
        return fmt.MISSING
    text = f"{fmt.number(speed, 1, lang)}"
    if gust is not None:
        text += f" ({fmt.number(gust, 1, lang)})"
    return text + " m/s"


def footer(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, lang: str = "en",
           left: str = "", theme: Theme | None = None) -> bool:
    """Status line. The render time is always shown, so a stale screen is visible (O4)."""
    t = theme or Theme()
    p = t.px
    b12, r12 = t.text("xs", bold=True), t.text("xs")
    svg.line(r.x, r.y, r.x + r.w, r.y, 2)
    right = f"{i18n.t(lang, "now.updated")} {snap.now:%Y-%m-%d %H:%M}"
    if snap.battery is not None:
        right = f"{i18n.t(lang, "now.battery")} {snap.battery} % · " + right
    base = r.y + r.h - p(7)
    if snap.stale_since:
        tag = f"{i18n.t(lang, "now.stale")} {snap.stale_since}"
        tw = measure.width(tag, b12) + p(8)
        svg.rect(r.x, r.y + p(3), tw, r.h - p(5), BLACK)
        svg.text(r.x + p(4), base, tag, b12, color="#fff")
        left_x = r.x + tw + p(8)
    else:
        left_x = r.x
    rw = measure.width(right, r12)
    svg.text(r.x + r.w, base, right, r12, "end")
    if left:
        svg.text(left_x, base, measure.truncate(left, r12, r.x + r.w - rw - p(12) - left_x),
                 r12)
    return True
