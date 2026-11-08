"""Daily forecast: calm week (no wind/rain shown) and a stormy, wet day (inverted)."""

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
from custom_components.paperboard.widgets_weather import daily
from tests.golden_util import assert_golden

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)
FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"


def _render(forecast: list[dict]) -> tuple[bool, bytes]:
    fx = json.loads(FIXTURE.read_text())
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="x",
                    states={"weather.forecast_home": fx["states"]["weather.forecast_home"]},
                    roles={"weather": "weather.forecast_home"}, forecasts={"daily": forecast})
    svg = Svg(800, 480)
    ok = daily(svg, Rect(0, 150, 432, 154), snap, Measurer(load_fonts()), Theme())
    return ok, render(str(svg), PanelProfile(), FONT_DIR).png


def test_calm_week_matches_owner_fixture() -> None:
    fx = json.loads(FIXTURE.read_text())["weather_forecasts"]["weather.forecast_home"]["daily"]
    ok, png = _render(fx)
    assert ok
    assert_golden("daily_calm", png)


def test_stormy_and_wet_days_inverted() -> None:
    fx = json.loads(FIXTURE.read_text())["weather_forecasts"]["weather.forecast_home"]["daily"]
    days = [dict(d) for d in fx]
    days[2]["wind_gust_speed"] = 72.0  # km/h -> 20 m/s
    days[4]["precipitation"] = 18.4
    ok, png = _render(days)
    assert ok
    assert_golden("daily_warnings", png)


def test_no_forecast_collapses() -> None:
    ok, _ = _render([])
    assert ok is False
