"""The empty-house gate (CI blocks on it): every widget and every bundled layout renders with
zero entities - and with garbage - without a single exception. The CO2 lesson, made permanent."""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

import custom_components.paperboard.widget_registry  # noqa: F401 - fills the registry
from custom_components.paperboard.compose import REGISTRY, render_spec
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layout_file import BUNDLED_DIR, load_all
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.prices import PriceSnapshot
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from tests.golden_util import assert_golden

NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))
MEASURE = Measurer(load_fonts())

EMPTY = Snapshot(lang="sv", now=NOW, width=800, height=480, screen_name="Tom")
GARBAGE_ROLES = {r: f"sensor.{r}" for r in (
    "weather", "outdoor_temp", "indoor_temp", "outdoor_humidity", "rain_today", "price",
    "solar_forecast_today", "solar_power", "grid_power", "house_power", "house_energy_today",
    "battery_soc", "battery_power", "sun")}
GARBAGE = Snapshot(lang="sv",
    now=NOW, width=800, height=480, screen_name="Skräp",
    roles={**GARBAGE_ROLES, "rooms": ["sensor.r1", None, 7], "calendars": ["calendar.x"]},
    states={f"sensor.{r}": {"state": s, "attributes": {"temperature": "x", "unit_of_measurement":
                                                       None, "raw_today": [{"start": None}]}}
            for r, s in zip(GARBAGE_ROLES, ["unavailable", "unknown", "", "nan", "inf"] * 3,
                            strict=False)},
    forecasts={"daily": [{"datetime": "nope"}, {}, {"datetime": "2026-11-09T00:00:00+00:00",
                                                     "temperature": "warm"}],
               "hourly": [None, {"datetime": 5}]},  # type: ignore[list-item]
    prices=PriceSnapshot(points=[], unit=None), events={"calendar.x": [{"all_day": True}]},
)


@pytest.mark.parametrize("snap", [EMPTY, GARBAGE], ids=["empty", "garbage"])
@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_every_widget_survives(name: str, snap: Snapshot) -> None:
    for theme in (Theme(), Theme(bit_depth=2)):
        result = REGISTRY[name](Svg(800, 480), Rect(16, 16, 400, 220), snap, MEASURE, theme, {})
        assert isinstance(result, bool)


def test_every_bundled_layout_renders_empty() -> None:
    loaded = load_all(None)
    assert not loaded.errors, loaded.errors
    for spec in loaded.layouts.values():
        for snap in (EMPTY, GARBAGE):
            notes: list[str] = []
            svg = render_spec(spec, snap, MEASURE, Theme(), notes)
            assert notes == [], f"{spec.name}: {notes}"
            render(svg, PanelProfile(), FONT_DIR)
        assert_golden(f"empty_{spec.name}",
                      render(render_spec(spec, EMPTY, MEASURE, Theme()), PanelProfile(),
                             FONT_DIR).png)


def test_bundled_dir_exists() -> None:
    assert BUNDLED_DIR.is_dir()
