"""Text slots: auto headline, HA template rendered in the loop, wrapping, broken template."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant.common import MockConfigEntry

from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_text import auto_headline, text_slot
from tests.golden_util import assert_golden

NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))
DAILY = json.loads((Path(__file__).parent / "fixtures/states/owner_2026-11-08.json")
                   .read_text())["weather_forecasts"]["weather.forecast_home"]["daily"]


def test_auto_headline_owner_day() -> None:
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="x", forecasts={"daily": DAILY})
    assert auto_headline(snap) == "Grått och uppehåll, 3–4 grader"


def test_text_golden() -> None:
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="x", forecasts={"daily": DAILY},
                    texts={"{{ x }}": "Ett längre stycke text som måste radbrytas snyggt "
                                      "inom sin ruta utan att flyta över kanten alls."})
    svg, m, t = Svg(800, 480), Measurer(load_fonts()), Theme()
    assert text_slot(svg, Rect(20, 20, 260, 80), snap, m, t, auto="headline")
    assert text_slot(svg, Rect(320, 20, 260, 120), snap, m, t, template="{{ x }}", size="s",
                     bold=False)
    assert text_slot(svg, Rect(20, 200, 260, 80), snap, m, t) is False
    assert_golden("text_slots", render(str(svg), PanelProfile(), FONT_DIR).png)


async def test_templates_render_in_loop(hass: HomeAssistant, monkeypatch) -> None:
    from custom_components.paperboard import layouts

    monkeypatch.setitem(layouts.LAYOUTS, "status", layouts.Layout(
        build=layouts.build_status, templates=("{{ 1 + 1 }}", "{{ broken(")))
    assert await async_setup_component(hass, "http", {})
    from custom_components.paperboard.const import DOMAIN, SUBENTRY_SCREEN
    from tests.conftest import SCREEN_DATA
    entry = MockConfigEntry(domain=DOMAIN, options={"refresh_rate": 900}, subentries_data=[
        ConfigSubentryData(data=SCREEN_DATA, subentry_type=SUBENTRY_SCREEN, title="Hallen",
                           unique_id=None, subentry_id="screen1")])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    texts = entry.runtime_data.renderers["screen1"]._render_templates()
    assert texts["{{ 1 + 1 }}"] == "2"
    assert texts["{{ broken("].startswith("⚠")
