"""Room list: friendly-name cleaning, labels override, columns, missing rooms."""

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
from custom_components.paperboard.widgets_values import room_name, rooms
from tests.golden_util import assert_golden

NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))
STATES = json.loads((Path(__file__).parent / "fixtures/states/owner_2026-11-08.json")
                    .read_text())["states"]
ROOMS = ["sensor.v1_koket_temp_temp", "sensor.tvrum_temp_temperatur", "sensor.hallen_temperatur",
         "sensor.v1_badrum_temphumid_temp", "sensor.v1_sovrum_a_temperatur",
         "sensor.v2_sovrum_b_temperatur", "sensor.v0_kallare_th_temp",
         "sensor.gone"]


def test_room_names() -> None:
    assert room_name(STATES["sensor.hallen_temperatur"], "x") == "Hallen"
    assert room_name(STATES["sensor.v1_sovrum_a_temperatur"], "x") == "Sovrum a"
    assert room_name(None, "sensor.v0_kallare") == "Kallare"


def test_rooms_golden() -> None:
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="x", states=STATES,
                    roles={"rooms": ROOMS})
    svg, m, t = Svg(800, 480), Measurer(load_fonts()), Theme()
    assert rooms(svg, Rect(20, 20, 220, 200), snap, m, t, title="INNE")
    labels = ["Kök", "Tv-rum", "Hallen", "Badrum", "Rum A", "Rum B", "Källare", "Vind"]
    assert rooms(svg, Rect(300, 20, 480, 120), snap, m, t, columns=2, labels=labels)
    assert_golden("rooms", render(str(svg), PanelProfile(), FONT_DIR).png)


def test_no_rooms_collapses() -> None:
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="x")
    assert rooms(Svg(800, 480), Rect(0, 0, 200, 100), snap, Measurer(load_fonts()),
                 Theme()) is False
