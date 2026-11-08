"""Energy flow (mockup 08): sun, grid and battery around the house.

Owner rule (vault, 2026-11-08): figures are placed BESIDE their circles, never on the arrows -
grid figure above, solar figure to the right with the SOL label to the left, battery figure
above. Absent nodes and their edges are simply not drawn.
"""

from __future__ import annotations

import math

from . import fmt
from .icons import icon
from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import Rect
from .widgets_values import kilowatts, role_value

LABELS = {"sv": {"sun": "SOL", "grid": "NÄT", "battery": "BATTERI", "title": "JUST NU · kW"},
          "en": {"sun": "SOLAR", "grid": "GRID", "battery": "BATTERY", "title": "NOW · kW"}}


def _arrow(svg: Svg, x1: float, y1: float, x2: float, y2: float, width: float,
           dashed: bool, r: float) -> None:
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    sx, sy, ex, ey = x1 + ux * (r + 2), y1 + uy * (r + 2), x2 - ux * (r + 4), y2 - uy * (r + 4)
    svg.line(sx, sy, ex, ey, width, dash="4 4" if dashed else None)
    head = 7 + width
    lx, ly = ex - ux * head - uy * head * 0.6, ey - uy * head + ux * head * 0.6
    rx, ry = ex - ux * head + uy * head * 0.6, ey - uy * head - ux * head * 0.6
    svg.path(f"M{ex:.1f},{ey:.1f}L{lx:.1f},{ly:.1f}L{rx:.1f},{ry:.1f}Z", fill="#000",
             stroke=None)


def energy_flow(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme) -> bool:
    lang = snap.lang
    lab = LABELS.get(lang, LABELS["en"])
    sun = kilowatts(*role_value(snap, "solar_power")) if snap.roles.get("solar_power") else None
    grid = kilowatts(*role_value(snap, "grid_power")) if snap.roles.get("grid_power") else None
    house = kilowatts(*role_value(snap, "house_power")) if snap.roles.get("house_power") else None
    bat_soc = role_value(snap, "battery_soc")[0] if snap.roles.get("battery_soc") else None
    bat_kw = kilowatts(*role_value(snap, "battery_power")) \
        if snap.roles.get("battery_power") else None
    has = {"sun": bool(snap.roles.get("solar_power")), "grid": bool(snap.roles.get("grid_power")),
           "battery": bool(snap.roles.get("battery_soc") or snap.roles.get("battery_power"))}
    if not any(has.values()):
        return False
    rad = min(29.0, r.w / 10, r.h / 7)
    cx = r.x + r.w / 2
    pos = {"house": (cx, r.y + r.h - rad - 6), "sun": (cx, r.y + rad + 24),
           "grid": (r.x + rad + 16, r.y + r.h * 0.52), "battery": (r.x + r.w - rad - 16,
                                                                     r.y + r.h * 0.52)}
    small, fig = theme.text("xs", bold=True), theme.text("m", bold=True)
    svg.text(r.x, r.y + 12, lab["title"], theme.text("xs", bold=True))
    # edges first, so circles sit on top of the line ends
    hx, hy = pos["house"]
    if has["sun"]:
        _arrow(svg, *pos["sun"], hx, hy, 3, False, rad)
    if has["grid"]:
        gx, gy = pos["grid"]
        importing = grid is None or grid >= 0
        a, b = ((gx, gy), (hx, hy)) if importing else ((hx, hy), (gx, gy))
        _arrow(svg, *a, *b, 5 if grid and abs(grid) >= 1 else 3, False, rad)
    if has["battery"]:
        bx, by = pos["battery"]
        charging = bat_kw is not None and bat_kw < 0
        a, b = ((hx, hy), (bx, by)) if charging else ((bx, by), (hx, hy))
        _arrow(svg, *a, *b, 1.5, not bat_kw, rad)
    # nodes, icons and figures beside them
    for node, name in (("sun", "solar-power-variant"), ("grid", "transmission-tower"),
                       ("battery", "battery-50")):
        if not has[node]:
            continue
        x, y = pos[node]
        svg.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="#fff" stroke="#000" '
                f'stroke-width="2.5"/>')
        icon(svg, name, x - rad * 0.55, y - rad * 0.62, rad * 1.1)
    svg.raw(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{rad:.1f}" fill="#000"/>')
    icon(svg, "home", hx - rad * 0.5, hy - rad * 0.75, rad, "#fff")
    svg.text(hx, hy + rad * 0.62, fmt.number(house, 1, lang), small, "middle", "#fff")
    if has["sun"]:
        x, y = pos["sun"]
        svg.text(x + rad + 8, y + 7, fmt.with_unit(sun, "kW", 1, lang), fig)
        svg.text(x - rad - 8, y + 5, lab["sun"], small, "end")
    if has["grid"]:
        x, y = pos["grid"]
        svg.text(x, y - rad - 8, fmt.with_unit(abs(grid) if grid is not None else None, "kW", 1,
                                               lang), fig, "middle")
        svg.text(x, y + rad + 16, lab["grid"], small, "middle")
    if has["battery"]:
        x, y = pos["battery"]
        soc = fmt.with_unit(bat_soc, "%", 0, lang) if bat_soc is not None else ""
        if snap.roles.get("battery_power"):
            above = fmt.with_unit(abs(bat_kw) if bat_kw is not None else None, "kW", 1, lang)
            label = f"{lab['battery']} {soc}".strip()
        else:  # no power sensor: the charge level is the figure worth showing
            above, label = soc or fmt.MISSING, lab["battery"]
        svg.text(x, y - rad - 8, above, fig, "middle")
        svg.text(x, y + rad + 16, label, small, "middle")
    return True
