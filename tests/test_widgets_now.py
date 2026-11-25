"""'now' layout: full data from the owner's fixture, and an empty house."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import REGISTRY
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import LAYOUTS, Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from tests.golden_util import assert_golden

FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))


@pytest.fixture(scope="module")
def measure() -> Measurer:
    return Measurer(load_fonts())


def _snap(states: dict, **kw) -> Snapshot:
    return Snapshot(lang="sv",
                    now=NOW, width=800, height=480, screen_name="Hallen", states=states, **kw)


def test_now_layout_full(measure: Measurer) -> None:
    states = json.loads(FIXTURE.read_text())["states"]
    weather = {"weather.forecast_home": states["weather.forecast_home"]}
    svg = LAYOUTS["now"].build(_snap(weather, battery=100), measure)
    assert_golden("now_full", render(svg, PanelProfile(), FONT_DIR).png)


def test_now_layout_empty_house(measure: Measurer) -> None:
    svg = LAYOUTS["now"].build(_snap({}), measure)
    assert_golden("now_empty", render(svg, PanelProfile(), FONT_DIR).png)


def test_now_layout_garbage_and_stale(measure: Measurer) -> None:
    junk = {"weather.x": {"state": "unavailable",
                          "attributes": {"temperature": "unknown", "humidity": None,
                                         "wind_speed": "nan", "pressure": "abc"}}}
    svg = LAYOUTS["now"].build(_snap(junk, stale_since="11:40"), measure)
    assert_golden("now_garbage_stale", render(svg, PanelProfile(), FONT_DIR).png)


def test_discover_picks_one_weather() -> None:
    ids = ["sensor.a", "weather.zeta", "weather.alpha"]
    assert LAYOUTS["now"].resolve(ids) == ("weather.alpha",)
    assert LAYOUTS["now"].resolve([]) == ()


@pytest.mark.parametrize(("widget", "uv", "shown"), [
    ("now", 6.7, "7"), ("now", None, None), ("now", "unknown", None),
    ("now_grid", 6.7, "7"), ("now_grid", None, None), ("now_grid", "unknown", "—"),
])
def test_uv_index_row(measure: Measurer, widget: str, uv: object, shown: str | None) -> None:
    attrs = {"temperature": 2.8} if uv is None else {"temperature": 2.8, "uv_index": uv}
    snap = _snap({"weather.home": {"state": "cloudy", "attributes": attrs}})
    svg = Svg(800, 480)
    rect = Rect(16, 16, 768, 124) if widget == "now_grid" else Rect(16, 16, 300, 300)
    assert REGISTRY[widget](svg, rect, snap, measure, Theme(), {"rows": ["uv_index"]})
    assert ("uv-index" in str(svg).lower()) is (shown is not None)
    assert shown is None or f">{shown}</text>" in str(svg)
