"""Header styles: line (default), masthead (02), titlebar (06)."""

import datetime as dt
from zoneinfo import ZoneInfo

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import REGISTRY
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from tests.golden_util import assert_golden


def test_header_variants_golden() -> None:
    snap = Snapshot(now=dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm")),
                    width=800, height=480, screen_name="Hallen", home_name="Hemma",
                    roles={"calendars": ["calendar.h"]},
                    events={"calendar.h": [{"all_day": True, "date": "2026-11-08",
                                            "summary": "Father's Day"}]})
    svg, m, t = Svg(800, 480), Measurer(load_fonts()), Theme()
    for i, style in enumerate(("line", "masthead", "titlebar")):
        assert REGISTRY["header"](svg, Rect(16, 20 + i * 80, 768, 50), snap, m, t,
                                  {"style": style, "badge": "none"})
    assert_golden("header_variants", render(str(svg), PanelProfile(), FONT_DIR).png)
