"""Tavlan-style black panel: now + energy stacked with a fixed height share."""


import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import render_spec
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layout_file import parse
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer
from tests.golden_util import assert_golden
from tests.test_layout_tidslinjen import owner_snapshot

PANEL = """
name: panel
grid:
  columns: [290, fr]
  rows: [fr]
  padding: [12, 18]
  areas: [now rest]
  frames: {now: panel}
widgets:
  - {type: now, area: now, height: 300,
     options: {rows: [indoor, feels_like, humidity, wind, rain_today]}}
  - {type: energy, area: now, options: {rows: [price_now, solar_expected_today, battery]}}
  - {type: rooms, area: rest, options: {title: INNE, columns: 2}}
"""


def test_panel_golden() -> None:
    notes: list[str] = []
    svg = render_spec(parse(PANEL, "x"), owner_snapshot(), Measurer(load_fonts()), Theme(),
                      notes)
    assert notes == []
    assert_golden("panel_now_energy", render(svg, PanelProfile(), FONT_DIR).png)
