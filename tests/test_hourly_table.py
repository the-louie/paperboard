"""Hourly table (Tavlan): owner data with prices; without prices the column is dropped."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.prices import PriceSnapshot, from_state
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_weather import hourly_table
from tests.golden_util import assert_golden

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)
FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"


def _snap(with_prices: bool) -> Snapshot:
    fx = json.loads(FIXTURE.read_text())
    st = fx["states"]
    hourly = fx["weather_forecasts"]["weather.forecast_home"]["hourly"]
    prices = PriceSnapshot.of(from_state(st["sensor.nordpool_kwh_se3_sek_2_10_025"], NOW)) \
        if with_prices else None
    return Snapshot(lang="sv", now=NOW, width=800, height=480, screen_name="x",
                    states={"weather.forecast_home": st["weather.forecast_home"]},
                    roles={"weather": "weather.forecast_home"},
                    forecasts={"hourly": hourly}, prices=prices)


def _png(snap: Snapshot) -> bytes:
    svg = Svg(800, 480)
    assert hourly_table(svg, Rect(300, 20, 490, 250), snap, Measurer(load_fonts()), Theme())
    return render(str(svg), PanelProfile(), FONT_DIR).png


def test_with_prices() -> None:
    assert_golden("hourly_table_prices", _png(_snap(True)))


def test_without_prices() -> None:
    assert_golden("hourly_table_no_prices", _png(_snap(False)))


def test_no_forecast_collapses() -> None:
    snap = Snapshot(lang="sv", now=NOW, width=800, height=480, screen_name="x")
    assert hourly_table(Svg(800, 480), Rect(0, 0, 400, 200), snap, Measurer(load_fonts()),
                        Theme()) is False
