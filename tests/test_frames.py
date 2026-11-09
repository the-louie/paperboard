"""Area frames, gaps and margins (Bento-style tiles)."""

import datetime as dt
from zoneinfo import ZoneInfo

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard.compose import invert_colors, render_spec
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.grid import Grid
from custom_components.paperboard.layout_file import parse
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer
from tests.golden_util import assert_golden

TILES = """
name: tiles
grid:
  columns: [200, fr, fr]
  rows: [fr, fr]
  gap: 6
  margin: 8
  padding: [8, 11]
  areas: [hero a b, hero c c]
  frames: {hero: inverted, a: rounded, b: rounded, c: box}
widgets:
  - {type: now, area: hero, options: {rows: [humidity]}}
  - {type: text, area: a, options: {auto: headline}}
  - {type: sun_moon, area: b}
  - {type: footer, area: c, options: {left: name}}
"""


def test_gap_geometry() -> None:
    g = Grid.build([100, "fr"], ["fr"], ["a b"], 306, 50, gap=6)
    assert g.rect("a").w == 100 and g.rect("b").x == 106 and g.rect("b").w == 200


def test_invert_colors() -> None:
    assert invert_colors('<rect fill="#000"/><text fill="#fff">') == \
        '<rect fill="#fff"/><text fill="#000">'


def test_tiles_golden() -> None:
    spec = parse(TILES, "x")
    snap = Snapshot(lang="sv",
                    now=dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm")),
                    width=800, height=480, screen_name="Hallen",
                    states={"weather.x": {"state": "cloudy",
                                          "attributes": {"temperature": 3.1, "humidity": 89}}},
                    forecasts={"daily": [{"datetime": "2026-11-08T11:00:00+00:00",
                                          "condition": "cloudy", "temperature": 4.9,
                                          "templow": 3.1, "precipitation": 0}]})
    notes: list[str] = []
    svg = render_spec(spec, snap, Measurer(load_fonts()), Theme(), notes)
    assert notes == []
    assert_golden("frames_tiles", render(svg, PanelProfile(), FONT_DIR).png)
