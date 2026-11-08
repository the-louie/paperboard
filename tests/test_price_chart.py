"""Price chart widget: owner data, tomorrow included, empty."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.prices import PriceSnapshot, from_state
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.timeaxis import TimeAxis
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_series import axis_labels, now_marker, price_chart
from tests.golden_util import assert_golden

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)
FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"


@pytest.fixture(scope="module")
def measure() -> Measurer:
    return Measurer(load_fonts())


def _draw(state: dict | None, measure: Measurer) -> tuple[bool, bytes]:
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="x",
                    prices=PriceSnapshot.of(from_state(state, NOW)))
    svg, theme = Svg(800, 480), Theme()
    axis = TimeAxis.from_now(NOW, 24, 60, 780)
    ok = price_chart(svg, Rect(8, 100, 772, 200), snap, measure, theme, axis)
    now_marker(svg, axis, 100, 300)
    axis_labels(svg, axis, 300, theme, "sv")
    return ok, render(str(svg), PanelProfile(), FONT_DIR).png


def test_owner_today_only(measure: Measurer) -> None:
    state = json.loads(FIXTURE.read_text())["states"]["sensor.nordpool_kwh_se3_sek_2_10_025"]
    ok, png = _draw(state, measure)
    assert ok
    assert_golden("price_chart_today", png)


def test_with_tomorrow(measure: Measurer) -> None:
    state = json.loads(FIXTURE.read_text())["states"]["sensor.nordpool_kwh_se3_sek_2_10_025"]
    attrs = dict(state["attributes"])
    attrs["raw_tomorrow"] = [{"start": f"2026-11-09T{h:02d}:00:00+01:00",
                              "end": f"2026-11-09T{h + 1:02d}:00:00+01:00" if h < 23
                              else "2026-11-10T00:00:00+01:00",
                              "value": 1.2 + (h % 7) * 0.2} for h in range(24)]
    ok, png = _draw({**state, "attributes": attrs}, measure)
    assert ok
    assert_golden("price_chart_tomorrow", png)


def test_no_prices_collapses(measure: Measurer) -> None:
    ok, _ = _draw(None, measure)
    assert ok is False
