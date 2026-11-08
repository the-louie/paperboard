"""Every HA weather condition has an icon; golden sheet at 24/32/48 px."""

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.icons import CONDITION_ICON, PATHS, UNKNOWN, weather_icon
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.svg import Svg
from tests.golden_util import assert_golden

HA_CONDITIONS = ("clear-night", "cloudy", "exceptional", "fog", "hail", "lightning",
                 "lightning-rainy", "partlycloudy", "pouring", "rainy", "snowy", "snowy-rainy",
                 "sunny", "windy", "windy-variant")


def test_all_conditions_mapped() -> None:
    assert set(HA_CONDITIONS) == set(CONDITION_ICON)
    assert all(name in PATHS for name in (*CONDITION_ICON.values(), UNKNOWN))


def test_icon_sheet_golden() -> None:
    svg = Svg(800, 480)
    for row, size in enumerate((24, 32, 48)):
        for col, cond in enumerate((*HA_CONDITIONS, "garbage")):
            weather_icon(svg, cond, 10 + col * 49, 20 + row * 80, size)
    assert_golden("weather_icons", render(str(svg), PanelProfile(), FONT_DIR).png)
