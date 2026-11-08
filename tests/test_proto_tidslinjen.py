"""T-13 go/no-go: the hand-built mockup 01 renders crisp and under the byte limit."""

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.pipeline import PanelProfile, render
from scripts.spikes.proto_tidslinjen import build, load_fixture
from tests.golden_util import assert_golden

FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))


def test_tidslinjen_prototype() -> None:
    frame = render(build(load_fixture(FIXTURE), NOW), PanelProfile(), FONT_DIR)
    assert len(frame.png) < 90_000
    assert_golden("proto_tidslinjen", frame.png)
