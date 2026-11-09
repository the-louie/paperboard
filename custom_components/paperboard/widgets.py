"""Widgets: draw one block of a layout into a rectangle. Pure functions (executor-safe).

Contract (docs/research report, "Missing sensors never crash anything"): a widget never raises
on missing or garbage data; a missing value renders as an em dash; a widget with nothing at all
to show draws nothing and returns False, so the grid (phase 2) can collapse it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import fmt
from .fonts import PIXEL_SEMIBOLD
from .layouts import Snapshot
from .svg import BLACK, Svg
from .text import Measurer, TextStyle

B12, R12 = TextStyle("TRMNL12", 700, 12), TextStyle("TRMNL12", PIXEL_SEMIBOLD, 12)
B16, R16 = TextStyle("TRMNL16", 700, 16), TextStyle("TRMNL16", PIXEL_SEMIBOLD, 16)
BIG = TextStyle("Inter", 700, 74)

CONDITION = {
    "sv": {"clear-night": "Klart", "cloudy": "Mulet", "fog": "Dimma", "hail": "Hagel",
           "lightning": "Åska", "lightning-rainy": "Åska och regn", "partlycloudy": "Halvklart",
           "pouring": "Skyfall", "rainy": "Regn", "snowy": "Snö", "snowy-rainy": "Snöblandat regn",
           "sunny": "Sol", "windy": "Blåsigt", "windy-variant": "Blåsigt",
           "exceptional": "Extremt"},
    "en": {"clear-night": "Clear", "cloudy": "Cloudy", "fog": "Fog", "hail": "Hail",
           "lightning": "Thunder", "lightning-rainy": "Thunder, rain",
           "partlycloudy": "Partly cloudy", "pouring": "Pouring", "rainy": "Rain",
           "snowy": "Snow", "snowy-rainy": "Sleet", "sunny": "Sunny", "windy": "Windy",
           "windy-variant": "Windy", "exceptional": "Exceptional"},
}
LABELS = {"sv": {"now": "UTE NU", "humidity": "Fukt", "wind": "Vind", "pressure": "Tryck",
                 "dew": "Daggpunkt", "updated": "uppdaterad", "stale": "GAMMAL BILD",
                 "battery": "batteri"},
          "en": {"now": "OUTSIDE", "humidity": "Humidity", "wind": "Wind", "pressure": "Pressure",
                 "dew": "Dew point", "updated": "updated", "stale": "STALE IMAGE",
                 "battery": "battery"}}


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


def now_block(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, lang: str = "sv") -> bool:
    """Outdoor now: big temperature, condition, and a key/value list. Every field optional."""
    condition, attrs = _weather(snap)
    temp = attrs.get("temperature")
    rows = [
        (LABELS[lang]["humidity"], fmt.with_unit(attrs.get("humidity"), "%", 0)),
        (LABELS[lang]["wind"], _wind(attrs, lang)),
        (LABELS[lang]["dew"], fmt.with_unit(attrs.get("dew_point"), "°")),
        (LABELS[lang]["pressure"], fmt.with_unit(attrs.get("pressure"), "hPa", 0)),
    ]
    rows = [(k, v) for k, v in rows if v != fmt.MISSING]
    if fmt.to_float(temp) is None and condition is None and not rows:
        return False
    svg.text(r.x, r.y + 12, LABELS[lang]["now"], B12)
    svg.text(r.x - 4, r.y + 82, fmt.with_unit(temp, "°"), BIG)
    label = CONDITION[lang].get(condition or "", "")
    if label:
        svg.text(r.x, r.y + 110, measure.truncate(label, R16, r.w), R16)
    y = r.y + 140
    for key, value in rows:
        if y > r.y + r.h - 4:
            break
        svg.text(r.x, y, key, R16)
        svg.text(r.x + r.w, y, measure.truncate(value, B16, r.w * 0.6), B16, "end")
        y += 21
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


def footer(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, lang: str = "sv",
           left: str = "") -> bool:
    """Status line. The render time is always shown, so a stale screen is visible (O4)."""
    svg.line(r.x, r.y, r.x + r.w, r.y, 2)
    right = f"{LABELS[lang]['updated']} {snap.now:%Y-%m-%d %H:%M}"
    if snap.battery is not None:
        right = f"{LABELS[lang]['battery']} {snap.battery} % · " + right
    base = r.y + r.h - 7
    if snap.stale_since:
        tag = f"{LABELS[lang]['stale']} {snap.stale_since}"
        tw = measure.width(tag, B12) + 8
        svg.rect(r.x, r.y + 3, tw, r.h - 5, BLACK)
        svg.text(r.x + 4, base, tag, B12, color="#fff")
        left_x = r.x + tw + 8
    else:
        left_x = r.x
    rw = measure.width(right, R12)
    svg.text(r.x + r.w, base, right, R12, "end")
    if left:
        svg.text(left_x, base, measure.truncate(left, R12, r.x + r.w - rw - 12 - left_x), R12)
    return True
