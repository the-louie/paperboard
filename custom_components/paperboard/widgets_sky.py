"""Sun and moon (mockups 04/07). Sun times are computed in the event loop with HA's own astral
helper (home location) and passed in the snapshot; the moon phase is plain arithmetic, so this
widget never lacks data."""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

from . import i18n
from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import Rect

SYNODIC = 29.530588853
NEW_MOON = dt.datetime(2000, 1, 6, 18, 14, tzinfo=dt.UTC)



def moon(now: dt.datetime) -> tuple[float, float]:
    """(age in days since new moon, illuminated fraction 0..1)."""
    age = ((now - NEW_MOON).total_seconds() / 86400) % SYNODIC
    return age, (1 - math.cos(2 * math.pi * age / SYNODIC)) / 2


def next_phase(now: dt.datetime, target: float) -> dt.datetime:
    age, _ = moon(now)
    return now + dt.timedelta(days=(target - age) % SYNODIC)


def sun_times(hass: Any, today: dt.date) -> dict[str, str] | None:
    """Event-loop helper: ISO sunrise/sunset today and yesterday from HA's astral data."""
    from homeassistant.helpers.sun import get_astral_event_date

    out = {}
    for key, event, day in (("rise", "sunrise", today), ("set", "sunset", today),
                            ("rise_y", "sunrise", today - dt.timedelta(days=1)),
                            ("set_y", "sunset", today - dt.timedelta(days=1))):
        when = get_astral_event_date(hass, event, day)
        if when is None:  # polar day/night
            return None
        out[key] = when.isoformat()
    return out


def _moon_glyph(svg: Svg, cx: float, cy: float, r: float, age: float) -> None:
    """Outline disc with the lit part filled black (ink = light on paper)."""
    svg.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#fff" stroke="#000" '
            'stroke-width="2"/>')
    phase = age / SYNODIC  # 0 new, 0.5 full
    k = math.cos(2 * math.pi * phase)  # terminator ellipse x-radius factor
    waxing = phase < 0.5
    sweep_outer = 1 if waxing else 0
    rx = abs(k) * r
    sweep_inner = (0 if waxing else 1) if k > 0 else (1 if waxing else 0)
    d = (f"M{cx:.1f},{cy - r:.1f} A{r:.1f},{r:.1f} 0 0 {sweep_outer} {cx:.1f},{cy + r:.1f} "
         f"A{rx:.1f},{r:.1f} 0 0 {sweep_inner} {cx:.1f},{cy - r:.1f}Z")
    svg.path(d, fill="#000", stroke=None)


def sun_moon(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
             show: str = "both") -> bool:
    """show: both (side by side), sun or moon (narrow tiles)."""
    lang, tz = snap.lang, snap.now.tzinfo
    t = i18n.group(lang, "sky")
    label, big, small = theme.text("xs", bold=True), theme.text("m", bold=True), theme.text("xs")
    half = r.w / 2
    p = theme.px
    sun_ok = bool(snap.sun) and show in ("both", "sun")
    if show == "sun" and not snap.sun:
        return False
    if sun_ok:
        rise, sset = (dt.datetime.fromisoformat(snap.sun[k]).astimezone(tz)
                      for k in ("rise", "set"))
        length = sset - rise
        prev = dt.datetime.fromisoformat(snap.sun["set_y"]) - \
            dt.datetime.fromisoformat(snap.sun["rise_y"])
        delta = round((length - prev).total_seconds() / 60)
        hours, mins = divmod(round(length.total_seconds() / 60), 60)
        svg.text(r.x, r.y + p(12), t["sun"], label)
        svg.text(r.x, r.y + p(36), f"{rise:%H:%M}–{sset:%H:%M}", big)
        sign = "−" if delta < 0 else "+"
        svg.text(r.x, r.y + p(54), f"{hours} h {mins:02d} min ({sign}{abs(delta)} min)", small)
    if show == "sun":
        return True
    age, lit = moon(snap.now)
    mx = r.x + (half if sun_ok else 0)
    svg.text(mx, r.y + p(12), t["moon"], label)
    _moon_glyph(svg, mx + p(10), r.y + p(29), p(10), age)
    svg.text(mx + p(26), r.y + p(36), f"{round(lit * 100)} %", big)
    upcoming = min((next_phase(snap.now, 0.0), t["new"]), (next_phase(snap.now, SYNODIC / 2),
                                                          t["full"]), key=lambda p: p[0])
    when = upcoming[0].astimezone(tz)
    short = i18n.tl(lang, "date.weekday_abbr_lower")[when.weekday()]
    svg.text(mx, r.y + p(54), f"{upcoming[1]} {short} {when.day}/{when.month}", small)
    return True
