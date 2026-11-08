"""Expected-solar chart stacked above the price chart on one axis (owner's rows 01/08)."""

import datetime as dt
import json
import math
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
from custom_components.paperboard.timeaxis import TimeAxis
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_series import (
    axis_labels,
    night_shading,
    nights,
    now_marker,
    price_chart,
    solar_chart,
)
from tests.golden_util import assert_golden

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 10, 15, tzinfo=TZ)
FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"
SUN = {"sun.sun": {"state": "above_horizon",
                   "attributes": {"next_setting": "2026-11-08T15:03:20+00:00",
                                  "next_rising": "2026-11-09T06:31:20+00:00"}}}


def _solar() -> SolarSnapshot:
    hours = []
    for h in range(7, 17):
        start = dt.datetime(2026, 11, 8, h, tzinfo=TZ)
        hours.append((start.isoformat(), round(700 * math.sin(math.pi * (h - 6.5) / 10), 1)))
    return SolarSnapshot(hours=hours, today_kwh=3.657)


def _snap(**kw) -> Snapshot:
    state = json.loads(FIXTURE.read_text())["states"]["sensor.nordpool_kwh_se3_sek_2_10_025"]
    return Snapshot(now=NOW, width=800, height=480, screen_name="x", states=SUN,
                    prices=PriceSnapshot.of(from_state(state, NOW)), **kw)


def test_stack_golden() -> None:
    measure, theme, svg = Measurer(load_fonts()), Theme(), Svg(800, 480)
    snap = _snap(solar=_solar())
    axis = TimeAxis.from_now(NOW, 24, 60, 780)
    night_shading(svg, snap, theme, axis, 40, 380, "sv")
    assert solar_chart(svg, Rect(8, 60, 772, 120), snap, measure, theme, axis)
    assert price_chart(svg, Rect(8, 200, 772, 180), snap, measure, theme, axis)
    now_marker(svg, axis, 40, 380)
    axis_labels(svg, axis, 380, theme, "sv")
    assert_golden("solar_price_stack", render(str(svg), PanelProfile(), FONT_DIR).png)


def test_solar_collapses_without_curve() -> None:
    measure, theme, svg = Measurer(load_fonts()), Theme(), Svg(800, 480)
    axis = TimeAxis.from_now(NOW, 24, 60, 780)
    snap = _snap(solar=SolarSnapshot(hours=[], today_kwh=3.6))
    assert solar_chart(svg, Rect(8, 60, 772, 120), snap, measure, theme, axis) is False
    assert solar_chart(svg, Rect(8, 60, 772, 120), _snap(), measure, theme, axis) is False


def test_nights_day_and_night() -> None:
    day = nights(_snap())
    assert day[0][0].hour == 15 and len(day) == 2
    night_snap = Snapshot(now=NOW, width=1, height=1, screen_name="x", states={"sun.sun": {
        "attributes": {"next_setting": "2026-11-09T15:00:00+00:00",
                       "next_rising": "2026-11-09T06:30:00+00:00"}}})
    assert nights(night_snap)[0][1].hour == 6
    assert nights(Snapshot(now=NOW, width=1, height=1, screen_name="x")) == []
