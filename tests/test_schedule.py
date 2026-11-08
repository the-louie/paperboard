"""Time-of-day schedules: Tavlan 07-08 on school days, night layout, refresh before switches."""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from custom_components.paperboard.layout_file import load_all, parse
from custom_components.paperboard.schedule import parse_schedule

TZ = ZoneInfo("Europe/Stockholm")
RAW = {"name": "hallen", "default": "tidslinjen", "schedule": [
    {"layout": "tavlan", "from": "07:00", "to": "08:00", "days": "weekdays",
     "when": "binary_sensor.skoldag"},
    {"layout": "natt", "from": "22:00", "to": "06:00", "refresh_rate": 3600}]}
SCHOOL = {"binary_sensor.skoldag": {"state": "on"}}
HOLIDAY = {"binary_sensor.skoldag": {"state": "off"}}


def at(day: int, hh: int, mm: int = 0) -> dt.datetime:
    return dt.datetime(2026, 11, day, hh, mm, tzinfo=TZ)  # 9 Nov 2026 is a Monday


@pytest.mark.parametrize(("now", "states", "expected"), [
    (at(9, 7, 30), SCHOOL, "tavlan"),
    (at(9, 7, 30), HOLIDAY, "tidslinjen"),
    (at(9, 7, 30), {}, "tidslinjen"),            # condition sensor missing: no match
    (at(8, 7, 30), SCHOOL, "tidslinjen"),        # Sunday
    (at(9, 8, 0), SCHOOL, "tidslinjen"),         # end is exclusive
    (at(9, 23, 0), {}, "natt"),
    (at(10, 2, 0), {}, "natt"),                  # after midnight, still the night entry
    (at(9, 6, 0), {}, "tidslinjen"),
])
def test_layout_at(now: dt.datetime, states: dict, expected: str) -> None:
    assert parse_schedule(RAW, "x").layout_at(now, states) == expected


def test_refresh_rate_wakes_after_switch() -> None:
    s = parse_schedule(RAW, "x")
    assert s.refresh_rate(at(9, 6, 50), SCHOOL, 900) == 10 * 60 + 30
    assert s.refresh_rate(at(9, 23, 0), {}, 900) == 3600
    assert s.refresh_rate(at(9, 12, 0), {}, 900) == 900


def test_schedule_file_validation(tmp_path, monkeypatch) -> None:
    from custom_components.paperboard import layout_file

    monkeypatch.setattr(layout_file, "BUNDLED_DIR", tmp_path / "b")
    (tmp_path / "b").mkdir()
    user = tmp_path / "u"
    user.mkdir()
    (user / "s.yaml").write_text("name: s\ndefault: nope\nschedule:\n  - {layout: nope}\n")
    result = load_all(user)
    assert "s" not in result.layouts
    assert any("unknown layout 'nope'" in e for e in result.errors[str(user / "s.yaml")])
    with pytest.raises(ValueError, match="HH:MM"):
        parse("name: s\ndefault: a\nschedule:\n  - {layout: a, from: '25:99'}\n", "x")


async def test_schedule_in_hub(hass, hass_client_no_auth, hass_tmp_config_dir) -> None:
    from pathlib import Path

    from homeassistant.config_entries import ConfigSubentryData
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant.common import MockConfigEntry

    from custom_components.paperboard.const import CONF_LAYOUT, DOMAIN, SUBENTRY_SCREEN
    from scripts.fake_trmnl import FakeTrmnl
    from tests.conftest import SCREEN_DATA

    hass.config.config_dir = hass_tmp_config_dir
    user = Path(hass_tmp_config_dir) / "paperboard"
    user.mkdir(exist_ok=True)
    (user / "hallen.yaml").write_text(
        "name: hallen\ndefault: tidslinjen\nschedule:\n"
        "  - {layout: status, from: '00:00', to: '00:00', when: binary_sensor.skoldag}\n")
    hass.states.async_set("binary_sensor.skoldag", "on")
    assert await async_setup_component(hass, "http", {})
    entry = MockConfigEntry(domain=DOMAIN, options={"refresh_rate": 900}, subentries_data=[
        ConfigSubentryData(data={**SCREEN_DATA, CONF_LAYOUT: "hallen"},
                           subentry_type=SUBENTRY_SCREEN, title="Hallen", unique_id=None,
                           subentry_id="screen1")])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    renderer = entry.runtime_data.renderers["screen1"]
    assert renderer.layout.schedule is not None
    assert "binary_sensor.skoldag" in renderer.entities
    first = entry.runtime_data.screens["screen1"].frame
    hass.states.async_set("binary_sensor.skoldag", "off")  # schedule falls back to default
    from datetime import timedelta

    from homeassistant.util import dt as dt_util
    from pytest_homeassistant.common import async_fire_time_changed
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.runtime_data.screens["screen1"].frame.sha != first.sha

    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    data = await dev.display()
    assert 60 <= data["refresh_rate"] <= 900
