"""Sun and moon: owner's day (8 Nov 2026, moon 3 %), polar fallback, sun_times in HA."""

import datetime as dt
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant

from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_sky import moon, sun_moon, sun_times
from tests.golden_util import assert_golden

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 10, 5, tzinfo=TZ)
SUN = {"rise": "2026-11-08T07:31:20+01:00", "set": "2026-11-08T16:03:20+01:00",
       "rise_y": "2026-11-07T07:29:00+01:00", "set_y": "2026-11-07T16:05:40+01:00"}


def test_moon_on_mockup_day() -> None:
    age, lit = moon(dt.datetime(2026, 11, 8, 9, 5, tzinfo=dt.UTC))
    assert 27.5 < age < 28.5 and round(lit * 100) == 3


def test_sun_moon_golden() -> None:
    svg, m, t = Svg(800, 480), Measurer(load_fonts()), Theme()
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="x", sun=SUN)
    assert sun_moon(svg, Rect(16, 20, 360, 64), snap, m, t)
    polar = Snapshot(now=NOW, width=800, height=480, screen_name="x", sun=None)
    assert sun_moon(svg, Rect(16, 120, 360, 64), polar, m, t)  # moon only, still drawn
    for i, day in enumerate((0, 4, 8, 15, 22)):
        when = dt.datetime(2026, 11, 10, 12, tzinfo=TZ) + dt.timedelta(days=day)
        sun_moon(svg, Rect(16 + i * 150, 220, 140, 64),
                 Snapshot(now=when, width=800, height=480, screen_name="x"), m, t)
    assert_golden("sun_moon", render(str(svg), PanelProfile(), FONT_DIR).png)


async def test_sun_times_from_ha(hass: HomeAssistant) -> None:
    times = sun_times(hass, dt.date(2026, 11, 8))
    assert times is not None and set(times) == {"rise", "set", "rise_y", "set_y"}
