"""Layout widget types (docs/design/layout-schema.md) wired to their drawing functions.

Importing this module fills compose.REGISTRY. Each adapter takes (svg, rect, snap, measure,
theme, options) and returns False when it has nothing to draw.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import fmt
from .compose import axis_for, widget
from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import CONDITION, LABELS, Rect, _ms
from .widgets_agenda import HOLIDAY_SV, agenda
from .widgets_almanac import date_block, week
from .widgets_flow import energy_flow
from .widgets_series import axis_labels, night_shading, now_marker, price_chart, solar_chart
from .widgets_sky import sun_moon
from .widgets_text import text_slot
from .widgets_values import energy, kv_list, role_value, room_name, rooms, stat
from .widgets_weather import _weather_attrs, daily, hourly_strip, hourly_table, tomorrow_at

WEEKDAY = {"sv": ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"],
           "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
MONTH = {"sv": ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti",
                "september", "oktober", "november", "december"],
         "en": ["January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December"]}


def _flag(snap: Snapshot) -> str:
    """Today's all-day event from the bound calendars (holiday names translated for sv)."""
    for cal in snap.roles.get("calendars") or []:
        for ev in snap.events.get(cal, []):
            if ev.get("all_day") and ev.get("date") == snap.now.date().isoformat():
                name = ev.get("summary", "")
                return HOLIDAY_SV.get(name, name) if snap.lang == "sv" else name
    return ""


def _hourly_at(snap: Snapshot, when: dt.datetime) -> dict[str, Any] | None:
    for item in snap.forecasts.get("hourly", []):
        if not isinstance(item, dict):
            continue
        try:
            if dt.datetime.fromisoformat(str(item["datetime"])) == when:
                return item
        except (KeyError, ValueError, TypeError):
            continue
    return None


@widget("header")
def _header(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    style = o.get("style", "line")
    if style == "masthead":
        return _masthead(svg, r, snap, m, t, o)
    if style == "titlebar":
        return _titlebar(svg, r, snap, m, t, o)
    lang = snap.lang
    title = f"{WEEKDAY[lang][snap.now.weekday()]} {snap.now.day} {MONTH[lang][snap.now.month - 1]}"
    big, rest = t.text("m", bold=True), t.text("m")
    base = r.y + r.h / 2 + 7
    svg.text(r.x, base, title, big)
    right_edge = r.x + r.w
    if o.get("badge", "tomorrow_07") == "tomorrow_07":
        target = (snap.now + dt.timedelta(days=1)).replace(hour=7, minute=0, second=0,
                                                           microsecond=0)
        item = _hourly_at(snap, target)
        if item is not None:
            value = fmt.with_unit(item.get("temperature"), "°", 1, lang)
            vstyle, lstyle = t.text("s", bold=True), t.text("s")
            label = "Imorgon kl 07" if lang == "sv" else "Tomorrow 07:00"
            bw = m.width(value, vstyle) + 14
            svg.rect(r.x + r.w - bw, r.y + r.h / 2 - 12, bw, 24, t.ink, rx=3)
            svg.text(r.x + r.w - bw / 2, base - 1, value, vstyle, "middle", t.paper)
            svg.text(r.x + r.w - bw - 8, base - 1, label, lstyle, "end")
            right_edge = r.x + r.w - bw - 16 - m.width(label, lstyle)
    extra = []
    if o.get("show_week", True):
        extra.append(f"{'v.' if lang == 'sv' else 'wk'} {snap.now.isocalendar().week}")
    if o.get("show_flag", True) and (flag := _flag(snap)):
        extra.append(flag)
    x = r.x + m.width(title + " ", big)
    while extra and x + m.width(" · ".join(extra), rest) > right_edge - 8:
        extra.pop()  # drop the holiday flag first, then the week number
    if extra:
        svg.text(x, base, " · ".join(extra), rest)
    return True


def _date_line(snap: Snapshot, o: dict, with_year: bool = False) -> tuple[str, str]:
    lang = snap.lang
    first = f"{WEEKDAY[lang][snap.now.weekday()]} {snap.now.day} {MONTH[lang][snap.now.month - 1]}"
    if with_year:
        first += f" {snap.now.year}"
    second = []
    if o.get("show_week", True):
        second.append(f"{'vecka' if lang == 'sv' else 'week'} {snap.now.isocalendar().week}")
    if o.get("show_flag", True) and (flag := _flag(snap)):
        second.append(flag)
    return first, " · ".join(second)


def _masthead(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    """Newspaper masthead (02 Tidningen): big name left, date block right, double rule."""
    name = str(o.get("title") or snap.home_name or snap.screen_name)
    first, second = _date_line(snap, o, with_year=True)
    small = t.text("s", bold=True)
    right_w = max(m.width(first, small), m.width(second, small))
    title_style = t.numeral("xl") if r.h >= 44 else t.numeral("l")
    svg.text(r.x, r.y + r.h - 9, m.truncate(name, title_style, r.w - right_w - 16), title_style)
    svg.text(r.x + r.w, r.y + r.h - 26, first, small, "end")
    svg.text(r.x + r.w, r.y + r.h - 9, second, small, "end")
    svg.line(r.x, r.y + r.h - 3, r.x + r.w, r.y + r.h - 3, 2)
    svg.line(r.x, r.y + r.h, r.x + r.w, r.y + r.h, 1)
    return True


def _titlebar(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    """TRMNL-style title bar (06): black rounded bar, title left, date/info right."""
    svg.rect(r.x, r.y, r.w, r.h, t.ink, rx=8)
    title = str(o.get("title") or snap.home_name or snap.screen_name)
    first, second = _date_line(snap, o)
    info = f"{first} · {second}" if second else first
    base = r.y + r.h / 2 + 6
    svg.text(r.x + 12, base, title, t.text("s", bold=True), color=t.paper)
    svg.text(r.x + r.w - 12, base, m.truncate(info, t.text("xs"), r.w / 2), t.text("xs"),
             "end", t.paper)
    return True


NOW_ROWS = {"sv": {"indoor": "Uterum", "feels_like": "Känns som", "humidity": "Fukt",
                   "wind": "Vind", "dew_point": "Daggpunkt", "pressure": "Tryck",
                   "rain_today": "Regn idag"},
            "en": {"indoor": "Indoor", "feels_like": "Feels like", "humidity": "Humidity",
                   "wind": "Wind", "dew_point": "Dew point", "pressure": "Pressure",
                   "rain_today": "Rain today"}}


@widget("now")
def _now(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    lang = snap.lang
    weather_state = snap.role_state("weather")
    attrs = _weather_attrs(snap)
    temp, _u = role_value(snap, "outdoor_temp")
    if temp is None:
        temp = fmt.to_float(attrs.get("temperature"))
    indoor_label = NOW_ROWS[lang]["indoor"]
    if snap.roles.get("indoor_temp"):
        indoor_label = room_name(snap.role_state("indoor_temp"), snap.roles["indoor_temp"]) \
            if o.get("indoor_label") is None else o["indoor_label"]
    values = {
        "indoor": fmt.with_unit(role_value(snap, "indoor_temp")[0], "°", 1, lang)
        if snap.roles.get("indoor_temp") else None,
        "feels_like": fmt.with_unit(role_value(snap, "feels_like")[0], "°", 1, lang)
        if snap.roles.get("feels_like") else
        fmt.with_unit(attrs.get("apparent_temperature"), "°", 1, lang)
        if "apparent_temperature" in attrs else None,
        "humidity": fmt.with_unit(role_value(snap, "outdoor_humidity")[0]
                                  if snap.roles.get("outdoor_humidity")
                                  else attrs.get("humidity"), "%", 0, lang),
        "wind": None, "dew_point": fmt.with_unit(attrs.get("dew_point"), "°", 1, lang)
        if "dew_point" in attrs else None,
        "pressure": fmt.with_unit(attrs.get("pressure"), "hPa", 0, lang)
        if "pressure" in attrs else None,
        "rain_today": fmt.with_unit(role_value(snap, "rain_today")[0], "mm", 1, lang)
        if snap.roles.get("rain_today") else None,
    }
    unit = attrs.get("wind_speed_unit")
    speed, gust = _ms(attrs.get("wind_speed"), unit), _ms(attrs.get("wind_gust_speed"), unit)
    if speed is not None:
        values["wind"] = (f"{fmt.number(speed, 1, lang)}"
                          + (f" ({fmt.number(gust, 1, lang)})" if gust is not None else "")
                          + " m/s")
    wanted = o.get("rows", ["indoor", "feels_like", "humidity", "wind", "rain_today"])
    rows = [(indoor_label if k == "indoor" else NOW_ROWS[lang].get(k, k), values[k])
            for k in wanted if values.get(k) not in (None, fmt.MISSING)]
    if temp is None and weather_state is None and not rows:
        return False
    svg.text(r.x, r.y + 12, LABELS[lang]["now"], t.text("xs", bold=True))
    hero = t.numeral("hero")
    svg.text(r.x - 4, r.y + 14 + hero.size * 0.92, fmt.with_unit(temp, "°", 1, lang), hero)
    summary = CONDITION[lang].get(str((weather_state or {}).get("state", "")), "")
    days = snap.forecasts.get("daily") or []
    if days:
        hi, lo = days[0].get("temperature"), days[0].get("templow")
        parts = [summary] if summary else []
        parts.append(f"max {fmt.with_unit(hi, '°', 1, lang)}")
        parts.append(f"{'natt' if lang == 'sv' else 'low'} {fmt.with_unit(lo, '°', 1, lang)}")
        summary = " · ".join(parts)
    sy = r.y + 14 + hero.size * 0.92 + 26  # clear margin under the numeral (owner, rows 01/03)
    if summary:
        svg.text(r.x, sy, m.truncate(summary, t.text("s"), r.w), t.text("s"))
    kv_list(svg, Rect(r.x, sy + 10, r.w, r.y + r.h - sy - 10), rows, m, t, dotted=False)
    return True


@widget("timeline")
def _timeline(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    series = o.get("series", ["solar_forecast", "price"])
    axis = axis_for(snap, r, int(o.get("hours", 24)))
    label_h = 24
    drawable = {"solar_forecast": bool(snap.solar and snap.solar.hours),
                "price": bool(snap.prices and snap.prices.points)}
    present = [s for s in series if drawable.get(s)]
    if not present:
        return False
    # Equal shares, solar a little shorter than price (estimate vs. money).
    weights = {"solar_forecast": 0.42, "price": 0.58}
    total = sum(weights[s] for s in present)
    top, avail = r.y, r.h - label_h
    if o.get("night", "dots") == "dots":
        night_shading(svg, snap, t, axis, top, top + avail, snap.lang)
    y = top + 14
    for name in present:
        h = (avail - 14) * weights[name] / total
        box = Rect(r.x, y, r.w, h - 6)
        if name == "solar_forecast":
            solar_chart(svg, box, snap, m, t, axis)
        else:
            price_chart(svg, box, snap, m, t, axis, int(o.get("cheapest_hours", 2)))
        y += h
    now_marker(svg, axis, top + 14, top + avail)
    axis_labels(svg, axis, top + avail, t, snap.lang, int(o.get("tick_every", 3)))
    return True


@widget("daily")
def _daily(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return daily(svg, r, snap, m, t, int(o.get("days", 6)), float(o.get("warn_gust_ms", 14)),
                 float(o.get("warn_rain_mm", 10)))


@widget("hourly_table")
def _hourly(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return hourly_table(svg, r, snap, m, t, int(o.get("hours", 10)))


@widget("energy")
def _energy(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    rows = o.get("rows") or ("price_now", "solar_expected_today", "solar_now", "house_now",
                             "battery")
    return energy(svg, r, snap, m, t, rows, bool(o.get("title", True)))


@widget("energy_flow")
def _flow(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return energy_flow(svg, r, snap, m, t)


@widget("rooms")
def _rooms(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return rooms(svg, r, snap, m, t, int(o.get("columns", 1)), o.get("labels"), o.get("title"))


@widget("stat")
def _stat(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return stat(svg, r, snap, m, t, str(o.get("role", "")), str(o.get("label", "")),
                o.get("unit"), int(o.get("decimals", 1)), str(o.get("size", "xl")))


@widget("sun_moon")
def _sky(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return sun_moon(svg, r, snap, m, t, str(o.get("show", "both")))


@widget("footer")
def _footer(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    lang = snap.lang
    left = ""
    if o.get("left", "rooms") == "rooms" and isinstance(snap.roles.get("rooms"), list):
        parts = []
        for eid in snap.roles["rooms"]:
            if not isinstance(eid, str):
                continue
            st = snap.states.get(eid)
            value = fmt.with_unit((st or {}).get("state"), "°", 1, lang)
            parts.append(f"{room_name(st, eid)} {value}")
        left = ("Inne: " if lang == "sv" else "Inside: ") + " · ".join(parts)
    elif o.get("left") == "name":
        left = snap.screen_name
    small = t.text("xs")
    right = f"{snap.now:%Y-%m-%d %H:%M}"
    if snap.battery is not None:
        right = f"{'batteri' if lang == 'sv' else 'battery'} {snap.battery} % · {right}"
    base = r.y + r.h / 2 + 4
    x = r.x
    if snap.stale_since:
        tag = f"{LABELS[lang]['stale']} {snap.stale_since}"
        tw = m.width(tag, t.text("xs", bold=True)) + 8
        svg.rect(x, r.y + 2, tw, r.h - 4, t.ink)
        svg.text(x + 4, base, tag, t.text("xs", bold=True), color=t.paper)
        x += tw + 8
    rw = m.width(right, small)
    svg.text(r.x + r.w, base, right, small, "end")
    if left:
        svg.text(x, base, m.truncate(left, small, r.x + r.w - rw - 12 - x), small)
    return True


@widget("agenda")
def _agenda(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return agenda(svg, r, snap, m, t, int(o.get("days", 7)), bool(o.get("title", True)))


@widget("text")
def _text(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return text_slot(svg, r, snap, m, t, o.get("template"), o.get("auto"),
                     str(o.get("size", "m")), bool(o.get("bold", True)),
                     int(o.get("max_lines", 3)))


@widget("hourly_strip")
def _strip(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return hourly_strip(svg, r, snap, m, t, int(o.get("hours", 12)), o.get("title"))


@widget("tomorrow")
def _tomorrow(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return tomorrow_at(svg, r, snap, m, t, int(o.get("hour", 7)))


@widget("date")
def _date(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return date_block(svg, r, snap, m, t, _flag(snap) if o.get("show_flag", True) else "")


@widget("week")
def _week(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    return week(svg, r, snap, m, t, int(o.get("days", 6)))


@widget("now_grid")
def _now_grid(svg: Svg, r: Rect, snap: Snapshot, m: Measurer, t: Theme, o: dict) -> bool:
    """Outdoor now as a big numeral plus a grid of label/value cells (07 Almanackan).
    The cells follow options.rows in order - the owner wants 'Uterum' last."""
    lang = snap.lang
    attrs = _weather_attrs(snap)
    temp, _u = role_value(snap, "outdoor_temp")
    if temp is None:
        temp = fmt.to_float(attrs.get("temperature"))
    cells = []
    wanted = o.get("rows", ["feels_like", "humidity", "wind", "pressure", "rain_today",
                            "tomorrow_07", "indoor"])
    target = (snap.now + dt.timedelta(days=1)).replace(hour=7, minute=0, second=0,
                                                       microsecond=0)
    unit = attrs.get("wind_speed_unit")
    for key in wanted:
        if key == "indoor" and snap.roles.get("indoor_temp"):
            label = o.get("indoor_label") or room_name(snap.role_state("indoor_temp"),
                                                       snap.roles["indoor_temp"])
            cells.append((label, fmt.with_unit(role_value(snap, "indoor_temp")[0], "°", 1, lang)))
        elif key == "feels_like" and snap.roles.get("feels_like"):
            cells.append((NOW_ROWS[lang]["feels_like"],
                          fmt.with_unit(role_value(snap, "feels_like")[0], "°", 1, lang)))
        elif key == "humidity" and (snap.roles.get("outdoor_humidity") or "humidity" in attrs):
            value = role_value(snap, "outdoor_humidity")[0] if snap.roles.get(
                "outdoor_humidity") else attrs.get("humidity")
            cells.append((NOW_ROWS[lang]["humidity"], fmt.with_unit(value, "%", 0, lang)))
        elif key == "wind" and (speed := _ms(attrs.get("wind_speed"), unit)) is not None:
            cells.append((NOW_ROWS[lang]["wind"], f"{fmt.number(speed, 1, lang)} m/s"))
        elif key == "pressure" and "pressure" in attrs:
            cells.append((NOW_ROWS[lang]["pressure"],
                          fmt.with_unit(attrs.get("pressure"), "hPa", 0, lang)))
        elif key == "rain_today" and snap.roles.get("rain_today"):
            cells.append((NOW_ROWS[lang]["rain_today"],
                          fmt.with_unit(role_value(snap, "rain_today")[0], "mm", 1, lang)))
        elif key == "tomorrow_07" and (item := _hourly_at(snap, target)) is not None:
            cells.append(("Imorgon 07" if lang == "sv" else "Tomorrow 07",
                          fmt.with_unit(item.get("temperature"), "°", 1, lang)))
    if temp is None and not cells:
        return False
    hero = t.numeral("xxl")
    hero_w = m.width("−00,0°", hero) + 12
    svg.text(r.x, r.y + 12, LABELS[lang]["now"], t.text("xs", bold=True))
    svg.text(r.x - 2, r.y + 18 + hero.size * 0.9, fmt.with_unit(temp, "°", 1, lang), hero)
    cond = CONDITION[lang].get(str((snap.role_state("weather") or {}).get("state", "")), "")
    if cond:
        svg.text(r.x, r.y + r.h - 4, cond, t.text("s"))
    svg.line(r.x + hero_w, r.y + 4, r.x + hero_w, r.y + r.h - 4, 1)
    cols = 4
    gx, gw = r.x + hero_w + 12, r.w - hero_w - 12
    cw, rh = gw / cols, (r.h - 4) / max(1, -(-len(cells) // cols))
    for i, (label, value) in enumerate(cells):
        cx, cy = gx + (i % cols) * cw, r.y + (i // cols) * rh
        svg.text(cx, cy + 14, m.truncate(label.upper(), t.text("xs", bold=True), cw - 6),
                 t.text("xs", bold=True))
        vstyle = t.text("m", bold=True) if m.fits(value, t.text("m", bold=True), cw - 6) \
            else t.text("s", bold=True)
        svg.text(cx, cy + 34, m.truncate(value, vstyle, cw - 6), vstyle)
    return True
