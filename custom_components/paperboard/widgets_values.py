"""Value widgets: generic stat, key/value list, and the energy rows (owner rows 02/03/05/06:
'expected solar today' instead of 'solar so far')."""

from __future__ import annotations

from typing import Any

from . import fmt
from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import Rect


def role_value(snap: Snapshot, role: str) -> tuple[float | None, str]:
    """Numeric value and unit of a single-entity role (None when missing or garbage)."""
    st = snap.role_state(role)
    if not st:
        return None, ""
    return fmt.to_float(st.get("state")), str(st.get("attributes", {}).get(
        "unit_of_measurement") or "")


def kilowatts(value: float | None, unit: str) -> float | None:
    if value is None:
        return None
    return {"W": value / 1000, "kW": value, "MW": value * 1000}.get(unit, value)


def kv_list(svg: Svg, r: Rect, rows: list[tuple[str, str]], measure: Measurer, theme: Theme,
            row_h: float = 21, dotted: bool = True) -> float:
    """Label left, value right-aligned; returns the height used. Rows past r are dropped."""
    label, value = theme.text("s"), theme.text("s", bold=True)
    y = r.y
    for i, (k, v) in enumerate(rows):
        if y + row_h > r.y + r.h + 2:
            break
        base = y + row_h - 6
        vw = measure.width(v, value)
        svg.text(r.x, base, measure.truncate(k, label, r.w - vw - 8), label)
        svg.text(r.x + r.w, base, v, value, "end")
        if dotted and i < len(rows) - 1:
            svg.line(r.x, y + row_h, r.x + r.w, y + row_h, 1, dash="1 2")
        y += row_h
    return y - r.y


def stat(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme, role: str,
         label: str, unit: str | None = None, decimals: int = 1, size: str = "xl") -> bool:
    """One labelled number; missing -> em dash (still drawn: the label tells what is missing)."""
    value, native_unit = role_value(snap, role)
    if snap.roles.get(role) is None:
        return False  # role not bound in this home: collapse
    text = fmt.with_unit(value, unit if unit is not None else native_unit, decimals, snap.lang)
    svg.text(r.x, r.y + 12, label.upper(), theme.text("xs", bold=True))
    svg.text(r.x - 2, r.y + 14 + theme.numeral(size).size * 0.9,
             measure.truncate(text, theme.numeral(size), r.w), theme.numeral(size))
    return True


ENERGY_LABELS = {
    "sv": {"price_now": "El nu", "solar_expected_today": "Sol idag förväntat",
           "solar_now": "Sol nu", "house_now": "Huset nu", "house_today": "Huset idag",
           "grid_now": "Nät nu", "battery": "Batteri", "title": "ENERGI"},
    "en": {"price_now": "Power price", "solar_expected_today": "Solar expected today",
           "solar_now": "Solar now", "house_now": "House now", "house_today": "House today",
           "grid_now": "Grid now", "battery": "Battery", "title": "ENERGY"},
}
DEFAULT_ENERGY_ROWS = ("price_now", "solar_expected_today", "solar_now", "house_now", "battery")


def energy_rows(snap: Snapshot) -> dict[str, str]:
    """Every energy row whose role is bound, formatted; unbound rows are absent."""
    lang = snap.lang
    out: dict[str, str] = {}
    if snap.roles.get("price"):
        current = snap.prices.current if snap.prices else None
        if current is None:
            current, _u = role_value(snap, "price")
        currency = (snap.prices.unit.split("/")[0] if snap.prices and snap.prices.unit else "")
        cur = {"SEK": "kr", "NOK": "kr", "DKK": "kr", "EUR": "€"}.get(currency, currency)
        out["price_now"] = f"{fmt.number(current, 2, lang)} {cur}".strip()
    if snap.roles.get("solar_forecast_today"):
        total = snap.solar.today_kwh if snap.solar else None
        out["solar_expected_today"] = fmt.with_unit(total, "kWh", 1, lang)
    for row, role in (("solar_now", "solar_power"), ("house_now", "house_power"),
                      ("grid_now", "grid_power")):
        if snap.roles.get(role):
            out[row] = fmt.with_unit(kilowatts(*role_value(snap, role)), "kW", 1, lang)
    if snap.roles.get("house_energy_today"):
        out["house_today"] = fmt.with_unit(role_value(snap, "house_energy_today")[0], "kWh", 0,
                                           lang)
    if snap.roles.get("battery_soc"):
        out["battery"] = fmt.with_unit(role_value(snap, "battery_soc")[0], "%", 0, lang)
    return out


def energy(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
           rows: tuple[str, ...] | list[str] = DEFAULT_ENERGY_ROWS, title: bool = True) -> bool:
    values = energy_rows(snap)
    labels: dict[str, Any] = ENERGY_LABELS.get(snap.lang, ENERGY_LABELS["en"])
    shown = [(labels[k], values[k]) for k in rows if k in values]
    if not shown:
        return False
    y = r.y
    if title:
        svg.text(r.x, r.y + 12, labels["title"], theme.text("xs", bold=True))
        y += 18
    kv_list(svg, Rect(r.x, y, r.w, r.h - (y - r.y)), shown, measure, theme)
    return True


_NOISE = {"temperatur", "temperature", "temp", "temp-fukt", "temphumid", "th", "sensor"}


def room_name(state: dict[str, Any] | None, entity_id: str) -> str:
    """A short room label from the friendly name: noise words and floor prefixes removed.
    Layouts can override with options.labels when a home's names are too odd."""
    raw = str((state or {}).get("attributes", {}).get("friendly_name") or entity_id.split(".")[-1])
    words = [w for w in raw.replace("_", " ").split()
             if w.lower() not in _NOISE and not (len(w) == 2 and w[0] in "vV" and w[1].isdigit())]
    name = " ".join(words) or raw
    return name[:1].upper() + name[1:]


def rooms(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme,
          columns: int = 1, labels: list[str] | None = None, title: str | None = None) -> bool:
    """Room temperatures in 1-3 columns; a missing room shows an em dash, no rooms collapses."""
    ids = snap.roles.get("rooms") or []
    if not isinstance(ids, list) or not ids:
        return False
    rows = []
    for i, eid in enumerate(ids):
        st = snap.states.get(eid)
        label = labels[i] if labels and i < len(labels) and labels[i] else room_name(st, eid)
        rows.append((label, fmt.with_unit((st or {}).get("state"), "°", 1, snap.lang)))
    y = r.y
    if title:
        svg.text(r.x, r.y + 12, title, theme.text("xs", bold=True))
        y += 18
    columns = max(1, min(3, columns))
    per = -(-len(rows) // columns)
    gap = 14
    cw = (r.w - gap * (columns - 1)) / columns
    for c in range(columns):
        chunk = rows[c * per:(c + 1) * per]
        kv_list(svg, Rect(r.x + c * (cw + gap), y, cw, r.h - (y - r.y)), chunk, measure, theme,
                row_h=19)
    return True
