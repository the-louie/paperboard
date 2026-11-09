"""T-13 prototype: mockup 01 "Tidslinjen" with the owner's changes, hand-built from a fixture.

Not the product: the layout engine (phase 2) replaces this. It exists to prove that the
pipeline renders the agreed design crisply and under the byte limit (go/no-go).

Owner's changes applied (vault row 01): no "Tryck" in the now block; the expected-solar graph
replaces the temperature/sun graph and shares the price graph's time axis.

PROTOTYPE APPROXIMATION: the owner's HA exposes no hourly solar forecast today (energy prefs
point at a removed config entry; see T-13 notes). The hourly curve is therefore a half-sine
between sunrise and sunset scaled to the real daily total (sensor.energy_production_today).
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
from functools import partial
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.paperboard import fmt as _fmt
from custom_components.paperboard.fonts import load_fonts
from custom_components.paperboard.svg import BLACK, WHITE, Svg
from custom_components.paperboard.text import Measurer, TextStyle


class fmt:  # noqa: N801 - the Sprint 01 prototype is the Swedish reference: Swedish numbers
    MISSING = _fmt.MISSING
    to_float = staticmethod(_fmt.to_float)
    number = staticmethod(partial(_fmt.number, lang="sv"))
    with_unit = staticmethod(partial(_fmt.with_unit, lang="sv"))

TZ = ZoneInfo("Europe/Stockholm")
ICON_DIR = Path(__file__).parent / "icons"
B12, R12 = TextStyle("TRMNL12", 700, 12), TextStyle("TRMNL12", 400, 12)
B16, R16 = TextStyle("TRMNL16", 700, 16), TextStyle("TRMNL16", 400, 16)
B21, R21 = TextStyle("TRMNL21", 700, 21), TextStyle("TRMNL21", 400, 21)
BIG = TextStyle("Inter", 700, 74)
MID = TextStyle("Inter", 700, 26)
MEASURE = Measurer(load_fonts())
DAYS = ["Mån", "Tis", "Ons", "Tor", "Fre", "Lör", "Sön"]
MONTHS = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti",
          "september", "oktober", "november", "december"]
ICON = {"cloudy": "weather-cloudy", "partlycloudy": "weather-partly-cloudy",
        "sunny": "weather-sunny", "rainy": "weather-rainy", "pouring": "weather-pouring",
        "snowy": "weather-snowy", "clear-night": "weather-night", "fog": "weather-fog"}
CONDITION_SV = {"cloudy": "Mulet", "partlycloudy": "Halvklart", "sunny": "Sol",
                "rainy": "Regn", "pouring": "Skyfall", "snowy": "Snö", "fog": "Dimma",
                "clear-night": "Klart"}


def icon(svg: Svg, condition: str, x: float, y: float, size: float) -> None:
    name = ICON.get(condition, "weather-cloudy")
    d = re.search(r' d="([^"]+)"', (ICON_DIR / f"{name}.svg").read_text()).group(1)
    s = size / 24
    svg.raw(f'<path transform="translate({x:.0f},{y:.0f}) scale({s:.3f})" d="{d}" '
            'fill="#000"/>')


def local(iso: str) -> dt.datetime:
    return dt.datetime.fromisoformat(iso).astimezone(TZ)


def build(fixture: dict, now: dt.datetime) -> str:
    st = fixture["states"]

    def val(entity: str) -> object:
        return st.get(entity, {}).get("state")

    hourly = fixture["weather_forecasts"]["weather.forecast_home"]["hourly"]
    daily = fixture["weather_forecasts"]["weather.forecast_home"]["daily"]
    svg = Svg(800, 480)

    # ---- header -------------------------------------------------------------------
    holiday = next((e["summary"] for e in fixture["calendar_events"].get(
        "calendar.holidays_in_sweden", []) if e["start"].get("date") == now.date().isoformat()),
        "")
    holiday = {"Father's Day": "Fars dag"}.get(holiday, holiday)
    weekday = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    title = f"{weekday[now.weekday()]} {now.day} {MONTHS[now.month - 1]}"
    svg.text(16, 27, title, B21)
    w = 16 + MEASURE.width(title + " ", B21)
    svg.text(w, 27, f"v. {now.isocalendar().week}" + (f" · {holiday}" if holiday else ""), R21)
    tomorrow7 = (now + dt.timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    t7 = next((h["temperature"] for h in hourly if local(h["datetime"]) == tomorrow7), None)
    svg.rect(728, 9, 60, 24, BLACK, rx=3)
    svg.text(758, 27, fmt.with_unit(t7, "°"), B16, "middle", WHITE)
    svg.text(720, 27, "Imorgon kl 07", R16, "end")
    svg.line(0, 39, 800, 39, 2)

    # ---- now block ------------------------------------------------------------------
    svg.line(250, 39, 250, 302, 2)
    svg.text(16, 58, "UTE NU", B12)
    svg.text(12, 128, fmt.with_unit(val("sensor.ecowitt_temp"), "°"), BIG)
    today = daily[0] if daily else {}
    cond = CONDITION_SV.get(str(val("weather.forecast_home")), "")
    svg.text(16, 158, f"{cond} · max {fmt.with_unit(today.get('temperature'), '°')} · "
             f"natt {fmt.with_unit(today.get('templow'), '°')}", R16)
    speed = fmt.to_float(val("sensor.ecowitt_windspeed"))
    gust = fmt.to_float(val("sensor.ecowitt_windgust"))
    wind = (f"{fmt.number(speed / 3.6 if speed is not None else None)} "
            f"({fmt.number(gust / 3.6 if gust is not None else None)}) m/s "
            f"{val('sensor.ecowitt_winddir_name') or ''}")
    rows = [("Uterum", fmt.with_unit(val("sensor.ecowitt_tempin"), "°")),
            ("Känns som", fmt.with_unit(val("sensor.ecowitt_feelslike"), "°")),
            ("Fukt", fmt.with_unit(val("sensor.ecowitt_humidity"), "%", 0)),
            ("Vind", wind.strip()),
            ("Regn idag", fmt.with_unit(val("sensor.ecowitt_dailyrain"), "mm"))]
    for i, (k, v) in enumerate(rows):
        y = 190 + i * 21
        svg.text(16, y, k, R16)
        svg.text(236, y, v, B16, "end")

    # ---- shared 24 h time axis: solar forecast above, price below -------------------
    x0, x1 = 286, 788
    start = now.replace(minute=0, second=0, microsecond=0)
    hours = 24
    cw = (x1 - x0) / hours

    def hx(t: dt.datetime) -> float:
        return x0 + (t - start).total_seconds() / 3600 * cw

    sunrise, sunset = local("2026-11-08T06:31:20+00:00"), local("2026-11-08T15:03:20+00:00")
    rise2 = sunrise + dt.timedelta(days=1)
    night_l, night_r = max(hx(sunset), x0), min(hx(rise2), x1)
    svg.rect(night_l, 48, night_r - night_l, 236, "dots")
    svg.rect(night_l + 2, 50, 74, 14, WHITE)
    svg.text(night_l + 4, 61, f"sol ned {sunset:%H:%M}", R12)
    svg.rect(night_r - 70, 50, 68, 14, WHITE)
    svg.text(night_r - 4, 61, f"upp {rise2:%H:%M}", R12, "end")

    # solar (approximation, see module docstring)
    total_kwh = fmt.to_float(val("sensor.energy_production_today")) or 0.0
    day_h = (sunset - sunrise).total_seconds() / 3600
    sol = []
    for h in range(hours):
        mid = start + dt.timedelta(hours=h, minutes=30)
        frac = (mid - sunrise).total_seconds() / 3600 / day_h
        sol.append(max(0.0, math.sin(math.pi * frac)) if 0 < frac < 1 and mid.date() == now.date()
                   else 0.0)
    scale = total_kwh / (sum(sol) or 1)
    sol_kwh = [s * scale for s in sol]
    s_top, s_bot = 84, 150
    smax = max(max(sol_kwh), 0.2)
    svg.text(258, 80, "SOL", B12)
    svg.text(258, 93, "kWh", R12)
    for h, v in enumerate(sol_kwh):
        if v <= 0:
            continue
        top = s_bot - (s_bot - s_top) * v / smax
        svg.rect(x0 + h * cw + 1, top, cw - 2, s_bot - top, "hatch", stroke=BLACK, stroke_width=1)
    remain = fmt.to_float(val("sensor.energy_production_today_remaining"))
    svg.rect(x0 + 11 * cw, 70, 200, 14, WHITE)
    svg.text(x0 + 11 * cw + 4, 81, f"förväntat idag {fmt.with_unit(total_kwh, 'kWh')}"
             + (f" · kvar {fmt.number(remain)}" if remain is not None else ""), B12)
    svg.line(x0, s_bot, x1, s_bot, 1)

    # price: hourly bars from 96 quarter-hours, cheapest 2 h window filled vs outlined
    np_attrs = st.get("sensor.nordpool_kwh_se3_sek_2_10_025", {}).get("attributes", {})
    quarters = [fmt.to_float(q) for q in (np_attrs.get("today") or [])]
    hourly_price = [sum(quarters[i:i + 4]) / 4 for i in range(0, len(quarters), 4)
                    if None not in quarters[i:i + 4]]
    p_top, p_bot = 178, 268
    svg.text(258, 186, "EL", B12)
    svg.text(258, 199, "kr", R12)
    remaining = [(h, hourly_price[h]) for h in range(start.hour, len(hourly_price))]
    if remaining:
        pmin, pmax = 1.5, max(max(p for _, p in remaining), 2.5)
        best = min(range(len(remaining) - 1), key=lambda i: remaining[i][1] + remaining[i + 1][1])
        cheap = {remaining[best][0], remaining[best + 1][0]}
        for h, p in remaining:
            i = h - start.hour
            top = p_bot - (p_bot - p_top) * (p - pmin) / (pmax - pmin)
            if h in cheap:
                svg.rect(x0 + i * cw + 1, top, cw - 2, p_bot - top, BLACK)
            else:
                svg.rect(x0 + i * cw + 2, top + 1, cw - 4, p_bot - top - 1, WHITE,
                         stroke=BLACK, stroke_width=1.5)
        ch = sorted(cheap)
        bx = x0 + (ch[0] - start.hour) * cw
        by = min(p_bot - (p_bot - p_top) * (hourly_price[c] - pmin) / (pmax - pmin)
                 for c in ch) - 8
        svg.path(f"M{bx + 1:.1f},{by + 5:.1f}V{by:.1f}H{bx + 2 * cw - 1:.1f}V{by + 5:.1f}",
                 width=2)
        avg = (hourly_price[ch[0]] + hourly_price[ch[1]]) / 2
        svg.text(bx + cw, by - 4, f"{ch[0]:02d}–{ch[1] + 1:02d} {fmt.number(avg, 2)}", B12,
                 "middle")
        svg.rect(x1 - 112, 186, 112, 30, WHITE)
        svg.text(x1 - 4, 198, "morgondagens pris", R12, "end")
        svg.text(x1 - 4, 212, "kommer ~13:00", R12, "end")
    svg.line(x0, p_bot, x1, p_bot, 2)
    for h in range(0, hours, 3):
        x = x0 + h * cw
        svg.line(x, p_bot, x, p_bot + 5, 2)
        svg.text(x, p_bot + 18, "nu" if h == 0 else f"{(start.hour + h) % 24:02d}",
                 B12 if h == 0 else R12, "middle")
    svg.line(x0 + 1, 48, x0 + 1, p_bot, 2, dash="3 3")
    svg.line(0, 302, 800, 302, 2)

    # ---- bottom: 6 days + energy ----------------------------------------------------
    for i, d in enumerate(daily[:6]):
        x = i * 72
        if i:
            svg.line(x, 302, x, 456, 1)
        when = local(d["datetime"])
        svg.text(x + 36, 322, "Idag" if i == 0 else DAYS[when.weekday()], B16, "middle")
        icon(svg, d.get("condition", ""), x + 20, 328, 32)
        svg.text(x + 36, 384, fmt.with_unit(d.get("temperature"), "°", 0), B21, "middle")
        svg.text(x + 36, 402, fmt.with_unit(d.get("templow"), "°", 0), R16, "middle")
        rain = fmt.to_float(d.get("precipitation"))
        svg.text(x + 36, 422, f"{fmt.number(rain)} mm" if rain else "–", R12, "middle")
    svg.line(432, 302, 432, 456, 2)
    svg.text(448, 322, "ENERGI", B12)
    np_now = fmt.to_float(val("sensor.nordpool_kwh_se3_sek_2_10_025"))
    house_w = fmt.to_float(val("sensor.house_usage_w"))
    pv_w = fmt.to_float(val("sensor.pv_1_power"))
    erows = [("El nu", f"{fmt.number(np_now, 2)} kr"),
             ("Sol idag förväntat", fmt.with_unit(total_kwh, "kWh")),
             ("Sol nu", fmt.with_unit(pv_w / 1000 if pv_w is not None else None, "kW")),
             ("Huset nu", fmt.with_unit(house_w / 1000 if house_w is not None else None, "kW")),
             ("Batteri", fmt.with_unit(val("sensor.battery_state_of_capacity"), "%", 0))]
    for i, (k, v) in enumerate(erows):
        y = 344 + i * 22
        svg.text(448, y, k, R16)
        svg.text(784, y, v, B16, "end")
        if i < len(erows) - 1:
            svg.line(448, y + 6, 784, y + 6, 1, dash="1 2")

    # ---- footer ---------------------------------------------------------------------
    svg.line(0, 456, 800, 456, 2)
    rooms = [("Kök", "sensor.v1_koket_temp_temp"), ("Tv-rum", "sensor.tvrum_temp_temperatur"),
             ("Hallen", "sensor.hallen_temperatur"), ("Badrum", "sensor.v1_badrum_temphumid_temp"),
             ("Rum A", "sensor.v1_sovrum_a_temperatur"),
             ("Rum B", "sensor.v2_sovrum_b_temperatur")]
    svg.text(16, 473, "Inne: " + " · ".join(f"{n} {fmt.with_unit(val(e), '°')}"
                                            for n, e in rooms), R12)
    svg.text(784, 473, f"{now:%Y-%m-%d %H:%M}", R12, "end")
    return str(svg)


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
