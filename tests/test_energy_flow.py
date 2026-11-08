"""Energy flow: all nodes (owner's data), no battery, nothing bound."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_flow import energy_flow
from tests.golden_util import assert_golden

NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))
STATES = json.loads((Path(__file__).parent / "fixtures/states/owner_2026-11-08.json")
                    .read_text())["states"]
ALL = {"solar_power": "sensor.pv_1_power", "grid_power": "sensor.ams_946c_p",
       "house_power": "sensor.house_usage_w", "battery_soc": "sensor.battery_state_of_capacity"}


def _snap(roles: dict) -> Snapshot:
    states = dict(STATES)
    states["sensor.ams_946c_p"] = {"state": "1603", "attributes": {"unit_of_measurement": "W"}}
    return Snapshot(now=NOW, width=800, height=480, screen_name="x", states=states, roles=roles)


def test_flow_golden() -> None:
    svg, m, t = Svg(800, 480), Measurer(load_fonts()), Theme()
    assert energy_flow(svg, Rect(0, 0, 300, 236), _snap(ALL), m, t)
    no_bat = {k: v for k, v in ALL.items() if k != "battery_soc"}
    assert energy_flow(svg, Rect(400, 0, 300, 236), _snap(no_bat), m, t)
    no_sun = {k: v for k, v in ALL.items() if k != "solar_power"}
    assert energy_flow(svg, Rect(0, 240, 300, 236), _snap(no_sun), m, t)
    assert_golden("energy_flow", render(str(svg), PanelProfile(), FONT_DIR).png)


def test_nothing_bound_collapses() -> None:
    assert energy_flow(Svg(800, 480), Rect(0, 0, 300, 236), _snap({}), Measurer(load_fonts()),
                       Theme()) is False
