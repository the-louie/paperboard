"""Energy rows bind to roles; unbound rows vanish; garbage becomes a dash."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.paperboard.data import SolarSnapshot
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.prices import PriceSnapshot, from_state
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_values import energy, energy_rows, stat

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)
FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"
ROLES = {"price": "sensor.nordpool_kwh_se3_sek_2_10_025",
         "solar_forecast_today": "sensor.energy_production_today",
         "solar_power": "sensor.pv_1_power", "house_power": "sensor.house_usage_w",
         "battery_soc": "sensor.battery_state_of_capacity"}


def _snap(roles: dict) -> Snapshot:
    st = json.loads(FIXTURE.read_text())["states"]
    return Snapshot(lang="sv",
                    now=NOW, width=800, height=480, screen_name="x", states=st, roles=roles,
                    prices=PriceSnapshot.of(from_state(st[ROLES["price"]], NOW)),
                    solar=SolarSnapshot(hours=[], today_kwh=3.657))


def test_owner_rows() -> None:
    rows = energy_rows(_snap(ROLES))
    assert rows["price_now"].endswith(" kr")
    assert rows["solar_expected_today"] == "3,7 kWh"
    assert rows["house_now"].endswith(" kW") and rows["battery"].endswith(" %")


def test_unbound_rows_vanish_and_collapse() -> None:
    assert energy_rows(_snap({})) == {}
    assert energy(Svg(800, 480), Rect(0, 0, 300, 150), _snap({}), Measurer(load_fonts()),
                  Theme()) is False


def test_energy_and_stat_golden() -> None:
    from tests.golden_util import assert_golden

    svg, m, t = Svg(800, 480), Measurer(load_fonts()), Theme()
    assert energy(svg, Rect(448, 310, 336, 140), _snap(ROLES), m, t)
    assert stat(svg, Rect(20, 20, 200, 80), _snap(ROLES), m, t, "battery_soc", "Batteri",
                decimals=0)
    roles = {**ROLES, "outdoor_temp": "sensor.does_not_exist"}
    assert stat(svg, Rect(240, 20, 200, 80), _snap(roles), m, t, "outdoor_temp", "Ute")
    assert stat(svg, Rect(460, 20, 200, 80), _snap(ROLES), m, t, "outdoor_temp", "Ute") is False
    assert_golden("energy_and_stat", render(str(svg), PanelProfile(), FONT_DIR).png)
