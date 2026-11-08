"""Type scale and fills per bit depth, plus a golden style sheet."""

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import SCALE, Theme
from custom_components.paperboard.svg import Svg
from tests.golden_util import assert_golden


def test_pixel_fonts_stay_native() -> None:
    assert Theme().text("s").size == 16
    big = Theme(scale_factor=1.8)
    assert big.text("xs").family == "TRMNL21"  # 12*1.8=21.6 -> nearest native 21
    assert big.text("hero").size == 133


def test_fills_by_depth() -> None:
    assert Theme(bit_depth=1).tint == "dots"
    assert Theme(bit_depth=2).tint.startswith("#")


def _sheet(theme: Theme) -> str:
    svg = Svg(800, 480)
    y = 30
    for name in SCALE:
        style = theme.text(name, bold=True)
        svg.text(16, y, f"{name} {style.family} {style.size}px Söndag 3,1°", style)
        y += style.size + 10
    for i, fill in enumerate((theme.tint, theme.past, theme.estimate, theme.ink)):
        svg.rect(500 + i * 70, 40, 60, 120, fill, stroke="#000", stroke_width=1)
    return str(svg)


def test_style_sheet_golden() -> None:
    assert_golden("style_sheet_1bit", render(_sheet(Theme()), PanelProfile(), FONT_DIR).png)
    assert_golden("style_sheet_2bit",
                  render(_sheet(Theme(bit_depth=2)), PanelProfile(bit_depth=2), FONT_DIR).png)
