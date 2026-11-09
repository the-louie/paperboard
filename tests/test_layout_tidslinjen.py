"""Sprint 02 demo: 01 Tidslinjen from YAML, through roles, on the owner's real data."""

import datetime as dt
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import render_spec
from custom_components.paperboard.data import SolarSnapshot
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layout_file import load_all
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.prices import PriceSnapshot, from_state
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer
from tests.golden_util import assert_golden

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)
FIXTURE = json.loads((Path(__file__).parent / "fixtures/states/owner_2026-11-08.json")
                     .read_text())
OWNER_ROLES = {
    "weather": "weather.forecast_home", "outdoor_temp": "sensor.ecowitt_temp",
    "indoor_temp": "sensor.ecowitt_tempin", "feels_like": "sensor.ecowitt_feelslike",
    "outdoor_humidity": "sensor.ecowitt_humidity", "rain_today": "sensor.ecowitt_dailyrain",
    "price": "sensor.nordpool_kwh_se3_sek_2_10_025",
    "solar_forecast_today": "sensor.energy_production_today",
    "solar_power": "sensor.pv_1_power", "house_power": "sensor.house_usage_w",
    "battery_soc": "sensor.battery_state_of_capacity", "sun": "sun.sun",
    "rooms": ["sensor.v1_koket_temp_temp", "sensor.tvrum_temp_temperatur",
              "sensor.hallen_temperatur", "sensor.v1_badrum_temphumid_temp",
              "sensor.v1_sovrum_a_temperatur",
              "sensor.v2_sovrum_b_temperatur"],
    "calendars": ["calendar.holidays_in_sweden", "calendar.family"],
}


def _solar_test_curve() -> SolarSnapshot:
    """The owner's HA has no hourly forecast yet (B-081): a sine curve scaled to the real total
    stands in for test data only."""
    hours = [(dt.datetime(2026, 11, 8, h, tzinfo=TZ).isoformat(),
              round(3657 / 10 * 1.55 * math.sin(math.pi * (h - 7) / 9), 1))
             for h in range(8, 16)]
    return SolarSnapshot(hours=hours, today_kwh=3.657)


def owner_snapshot(**kw) -> Snapshot:
    st = dict(FIXTURE["states"])
    st["sun.sun"] = {"state": "above_horizon",
                     "attributes": {"next_setting": "2026-11-08T15:03:20+00:00",
                                    "next_rising": "2026-11-09T06:31:20+00:00"}}
    events = {"calendar.holidays_in_sweden": [
        {"all_day": True, "date": "2026-11-08", "start": "2026-11-08", "summary": "Father's Day"}],
        "calendar.family": [{"all_day": False, "start": "2026-11-09T10:30:00+01:00",
                             "summary": "Jobb"},
                            {"all_day": False, "start": "2026-11-10T09:00:00+01:00",
                             "summary": "Jobb"}]}
    kw.setdefault("lang", "sv")  # the owner goldens are the Swedish reference
    return Snapshot(now=NOW, width=800, height=480, screen_name="Hallen", states=st,
                    roles=OWNER_ROLES, battery=100,
                    forecasts=FIXTURE["weather_forecasts"]["weather.forecast_home"],
                    prices=PriceSnapshot.of(from_state(st[OWNER_ROLES["price"]], NOW)),
                    solar=_solar_test_curve(), events=events,
                    sun={"rise": "2026-11-08T07:31:20+01:00", "set": "2026-11-08T16:03:20+01:00",
                         "rise_y": "2026-11-07T07:29:00+01:00",
                         "set_y": "2026-11-07T16:05:40+01:00"}, **kw)


# The owner's data with English room, calendar and screen names (README images, English
# goldens): Swedish data must not trip the "no Swedish in English" checks.
EN_NAMES = {
    "sensor.v1_koket_temp_temp": "Kitchen", "sensor.tvrum_temp_temperatur": "TV room",
    "sensor.hallen_temperatur": "Hall", "sensor.v1_badrum_temphumid_temp": "Bathroom",
    "sensor.v1_sovrum_a_temperatur": "Bedroom A", "sensor.v2_sovrum_b_temperatur": "Bedroom B",
    "sensor.ecowitt_tempin": "Sunroom",
}
EN_SUMMARIES = {"Jobb": "Work"}
# The energy layout also reads the grid meter and the house's energy today (Sprint 03 T-13).
ENERGY_ROLES = {"grid_power": "sensor.power_meter_active_power",
                "house_energy_today": "sensor.house_load_today", "grid_export_positive": True}


def for_layout(name: str, snap: Snapshot) -> Snapshot:
    """The owner snapshot as each bundled layout's golden uses it."""
    import dataclasses

    if name == "energi":
        return dataclasses.replace(snap, roles={**snap.roles, **ENERGY_ROLES})
    return snap


def english_owner_snapshot(**kw) -> Snapshot:
    import copy
    import dataclasses

    snap = owner_snapshot(**{"lang": "en", **kw})
    states = copy.deepcopy(snap.states)
    for entity, name in EN_NAMES.items():
        states[entity]["attributes"]["friendly_name"] = name
    events = {cal: [{**e, "summary": EN_SUMMARIES.get(e.get("summary"), e.get("summary"))}
                    for e in evs] for cal, evs in snap.events.items()}
    return dataclasses.replace(snap, states=states, events=events, screen_name="Hall")


def test_tidslinjen_owner_1bit() -> None:
    spec = load_all(None).layouts["tidslinjen"]
    notes: list[str] = []
    svg = render_spec(spec, owner_snapshot(), Measurer(load_fonts()), Theme(), notes)
    assert notes == []
    frame = render(svg, PanelProfile(), FONT_DIR)
    assert len(frame.png) < 90_000
    assert_golden("tidslinjen_owner", frame.png)


def test_tidslinjen_owner_2bit() -> None:
    spec = load_all(None).layouts["tidslinjen"]
    svg = render_spec(spec, owner_snapshot(), Measurer(load_fonts()), Theme(bit_depth=2))
    assert_golden("tidslinjen_owner_2bit", render(svg, PanelProfile(bit_depth=2), FONT_DIR).png)


def test_tidslinjen_owner_4bit() -> None:
    spec = load_all(None).layouts["tidslinjen"]
    svg = render_spec(spec, owner_snapshot(), Measurer(load_fonts()), Theme(bit_depth=4))
    frame = render(svg, PanelProfile(bit_depth=4, byte_limit=750_000), FONT_DIR)
    assert_golden("tidslinjen_owner_4bit", frame.png)
