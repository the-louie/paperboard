"""05 Tavlan on the owner's data, at 07:05 on a school morning (Sprint 03 demo)."""

import datetime as dt
from zoneinfo import ZoneInfo

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import render_spec
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layout_file import load_all
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer
from tests.golden_util import assert_golden
from tests.test_layout_tidslinjen import owner_snapshot


def test_tavlan_owner() -> None:
    spec = load_all(None).layouts["tavlan"]
    notes: list[str] = []
    snap = owner_snapshot()
    frame = render(render_spec(spec, snap, Measurer(load_fonts()), Theme(), notes),
                   PanelProfile(), FONT_DIR)
    assert notes == [] and len(frame.png) < 90_000
    assert_golden("tavlan_owner", frame.png)


def test_tavlan_is_a_morning_board() -> None:
    assert load_all(None).layouts["tavlan"].clock_resolution == 300
    _ = dt.datetime(2026, 11, 9, 7, 5, tzinfo=ZoneInfo("Europe/Stockholm"))
