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
from .widgets_agenda import agenda
from .widgets_flow import energy_flow
from .widgets_series import axis_labels, night_shading, now_marker, price_chart, solar_chart
from .widgets_sky import sun_moon
from .widgets_text import text_slot
from .widgets_values import energy, kv_list, role_value, room_name, rooms, stat
from .widgets_weather import _weather_attrs, daily, hourly_table

WEEKDAY = {"sv": ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"],
           "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
MONTH = {"sv": ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti",
                "september", "oktober", "november", "december"],
         "en": ["January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December"]}
HOLIDAY_SV = {"Father's Day": "Fars dag", "Mother's Day": "Mors dag",
              "Christmas Eve": "Julafton", "Christmas Day": "Juldagen",
              "New Year's Eve": "Nyårsafton", "New Year's Day": "Nyårsdagen",
              "Midsummer Eve": "Midsommarafton", "Midsummer Day": "Midsommardagen",
              "Easter Sunday": "Påskdagen", "Good Friday": "Långfredagen",
              "National Day of Sweden": "Sveriges nationaldag",
              "All Saints' Day": "Alla helgons dag"}


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
    lang = snap.lang
    title = f"{WEEKDAY[lang][snap.now.weekday()]} {snap.now.day} {MONTH[lang][snap.now.month - 1]}"
    big, rest = t.text("m", bold=True), t.text("m")
    base = r.y + r.h / 2 + 7
    svg.text(r.x, base, title, big)
    extra = []
    if o.get("show_week", True):
        extra.append(f"{'v.' if lang == 'sv' else 'wk'} {snap.now.isocalendar().week}")
    if o.get("show_flag", True) and (flag := _flag(snap)):
        extra.append(flag)
    if extra:
        svg.text(r.x + m.width(title + " ", big), base, " · ".join(extra), rest)
    if o.get("badge", "tomorrow_07") == "tomorrow_07":
        target = (snap.now + dt.timedelta(days=1)).replace(hour=7, minute=0, second=0,
                                                           microsecond=0)
        item = _hourly_at(snap, target)
        if item is not None:
            value = fmt.with_unit(item.get("temperature"), "°", 1, lang)
            vstyle = t.text("s", bold=True)
            bw = m.width(value, vstyle) + 14
            svg.rect(r.x + r.w - bw, r.y + r.h / 2 - 12, bw, 24, t.ink, rx=3)
            svg.text(r.x + r.w - bw / 2, base - 1, value, vstyle, "middle", t.paper)
            svg.text(r.x + r.w - bw - 8, base - 1,
                     "Imorgon kl 07" if lang == "sv" else "Tomorrow 07:00", t.text("s"), "end")
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
    return sun_moon(svg, r, snap, m, t)


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
