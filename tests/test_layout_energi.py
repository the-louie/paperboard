"""08 Energi on the owner's data (Sprint 03 demo)."""

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import render_spec
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layout_file import load_all
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer
from tests.golden_util import assert_golden
from tests.test_layout_tidslinjen import for_layout, owner_snapshot


def test_energi_owner() -> None:
    spec = load_all(None).layouts["energi"]
    snap = for_layout("energi", owner_snapshot())
    notes: list[str] = []
    frame = render(render_spec(spec, snap, Measurer(load_fonts()), Theme(), notes),
                   PanelProfile(), FONT_DIR)
    assert notes == [] and len(frame.png) < 90_000
    assert_golden("energi_owner", frame.png)
