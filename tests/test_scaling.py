"""Layouts designed at 800x480 scale to big panels (TRMNL X 1872x1404) without errors."""

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import render_spec
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layout_file import load_all
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer
from tests.golden_util import assert_golden
from tests.test_layout_tidslinjen import owner_snapshot


def test_every_layout_on_trmnl_x() -> None:
    measure = Measurer(load_fonts())
    big = owner_snapshot()
    big = type(big)(**{**big.__dict__, "width": 1872, "height": 1404})
    for name, spec in load_all(None).layouts.items():
        if not hasattr(spec, "grid"):
            continue
        notes: list[str] = []
        svg = render_spec(spec, big, measure, Theme(bit_depth=4), notes)
        assert notes == [], (name, notes)
        frame = render(svg, PanelProfile(1872, 1404, 4, 750_000), FONT_DIR)
        if name == "tidslinjen":
            assert_golden("tidslinjen_trmnl_x", frame.png)
