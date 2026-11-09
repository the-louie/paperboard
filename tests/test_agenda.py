"""Calendar agenda and its data cache."""

import datetime as dt
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from custom_components.paperboard.data import CalendarCache
from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.style import Theme
from custom_components.paperboard.svg import Svg
from custom_components.paperboard.text import Measurer
from custom_components.paperboard.widgets import Rect
from custom_components.paperboard.widgets_agenda import agenda
from tests.golden_util import assert_golden

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)
EVENTS = {"calendar.family": [
    {"start": "2026-11-08", "end": "2026-11-09", "summary": "Fars dag", "all_day": True},
    {"start": "2026-11-09T10:30:00+01:00", "end": "x", "summary": "Jobb"},
    {"start": "2026-11-10T09:00:00+01:00", "end": "x",
     "summary": "Tandläkare med en väldigt lång beskrivning som inte får plats"},
    {"start": "2026-11-11T08:00:00+01:00", "end": "x", "summary": "Jobb"},
    {"start": "2026-11-30T08:00:00+01:00", "end": "x", "summary": "för långt bort"}]}


def test_agenda_golden() -> None:
    snap = Snapshot(lang="sv", now=NOW, width=800, height=480, screen_name="x",
                    roles={"calendars": ["calendar.family"]}, events=EVENTS)
    svg = Svg(800, 480)
    assert agenda(svg, Rect(20, 20, 260, 300), snap, Measurer(load_fonts()), Theme())
    empty = Snapshot(lang="sv", now=NOW, width=800, height=480, screen_name="x",
                     roles={"calendars": ["calendar.family"]})
    assert agenda(svg, Rect(320, 20, 260, 80), empty, Measurer(load_fonts()), Theme())
    assert_golden("agenda", render(str(svg), PanelProfile(), FONT_DIR).png)


def test_agenda_collapses_without_calendars() -> None:
    snap = Snapshot(lang="sv", now=NOW, width=800, height=480, screen_name="x")
    assert agenda(Svg(800, 480), Rect(0, 0, 200, 200), snap, Measurer(load_fonts()),
                  Theme()) is False


async def test_calendar_cache(hass: HomeAssistant) -> None:
    async def handler(call: ServiceCall):
        return {e: {"events": [{"start": "2026-11-08", "end": "2026-11-09",
                                "summary": "Fars dag"},
                               {"start": "2026-11-09T10:30:00+01:00",
                                "end": "2026-11-09T18:00:00+01:00", "summary": "Jobb"}]}
                for e in call.data["entity_id"]}

    hass.services.async_register("calendar", "get_events", handler,
                                 supports_response=SupportsResponse.ONLY)
    cache = CalendarCache(hass, ["calendar.family", None])  # type: ignore[list-item]
    await cache.async_refresh()
    rows = cache.events["calendar.family"]
    assert rows[0]["all_day"] is True and rows[0]["date"] == "2026-11-08"
    assert rows[1]["all_day"] is False
