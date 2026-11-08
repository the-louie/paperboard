"""Text slots (mockup 02's headline): an HA template rendered in the event loop, or an
automatic weather headline built from the forecast - wrapped to the area by measured width."""

from __future__ import annotations

from . import fmt
from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import Rect

HEADLINE = {"sv": {"cloudy": "Grått", "partlycloudy": "Växlande molnighet", "sunny": "Soligt",
                   "clear-night": "Klart", "rainy": "Regnigt", "pouring": "Skyfall",
                   "snowy": "Snö", "snowy-rainy": "Snöblandat", "fog": "Dimmigt",
                   "windy": "Blåsigt", "lightning": "Åska", "lightning-rainy": "Åska och regn",
                   "dry": "uppehåll", "rain": "{mm} mm regn", "deg": "{lo}–{hi} grader"},
            "en": {"cloudy": "Grey", "partlycloudy": "Mixed clouds", "sunny": "Sunny",
                   "clear-night": "Clear", "rainy": "Rainy", "pouring": "Downpours",
                   "snowy": "Snow", "snowy-rainy": "Sleet", "fog": "Foggy", "windy": "Windy",
                   "lightning": "Thunder", "lightning-rainy": "Thunder and rain",
                   "dry": "dry", "rain": "{mm} mm of rain", "deg": "{lo} to {hi} degrees"}}


def auto_headline(snap: Snapshot) -> str:
    days = [d for d in snap.forecasts.get("daily", []) if isinstance(d, dict)]
    if not days:
        return ""
    today = days[0]
    words = HEADLINE.get(snap.lang, HEADLINE["en"])
    parts = []
    if (cond := words.get(str(today.get("condition")))) is not None:
        parts.append(cond)
    rain = fmt.to_float(today.get("precipitation"))
    parts.append(words["rain"].format(mm=fmt.number(rain, 0, snap.lang)) if rain and rain >= 1
                 else words["dry"])
    lo, hi = fmt.to_float(today.get("templow")), fmt.to_float(today.get("temperature"))
    if lo is not None and hi is not None:
        parts.append(words["deg"].format(lo=fmt.number(lo, 0, snap.lang),
                                         hi=fmt.number(hi, 0, snap.lang)))
    text = ", ".join(p for p in [" och ".join(parts[:2]) if snap.lang == "sv"
                                 else " and ".join(parts[:2]), *parts[2:]] if p)
    return text[:1].upper() + text[1:]


def text_slot(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
              template: str | None = None, auto: str | None = None, size: str = "m",
              bold: bool = True, max_lines: int = 3) -> bool:
    if template is not None:
        content = snap.texts.get(template, "")
    elif auto == "headline":
        content = auto_headline(snap)
    else:
        content = ""
    content = " ".join(content.split())
    if not content:
        return False
    style = theme.numeral(size) if size in ("l", "xl", "xxl", "hero") else theme.text(size, bold)
    line_h = style.size * 1.15
    lines = measure.wrap(content, style, r.w, max(1, min(max_lines, int(r.h // line_h))))
    for i, line in enumerate(lines):
        svg.text(r.x, r.y + style.size + i * line_h, line, style)
    return bool(lines)
