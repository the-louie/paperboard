"""Missed check-in turns on after 3 x refresh rate without a poll, off again on a poll."""

from datetime import timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import async_fire_time_changed

from scripts.fake_trmnl import FakeTrmnl

ENTITY = "binary_sensor.hallen_missed_check_in"
CHECKIN = "sensor.hallen_last_check_in"


async def test_missed_checkin(hass: HomeAssistant, freezer: FrozenDateTimeFactory, hub_entry,
                              hass_client_no_auth) -> None:
    assert hass.states.get(ENTITY).state == "off"
    assert hass.states.get(ENTITY).attributes["allowed_seconds"] == 2700

    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    await dev.display()

    freezer.tick(timedelta(seconds=2650))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "off"

    freezer.tick(timedelta(seconds=120))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "on"

    await dev.display()
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "off"


async def test_never_seen_device_is_a_problem(hass: HomeAssistant,
                                              freezer: FrozenDateTimeFactory,
                                              hub_entry) -> None:
    freezer.tick(timedelta(seconds=2701))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "on"


async def test_allowance_follows_the_rate_given_to_the_device(
        hass: HomeAssistant, freezer: FrozenDateTimeFactory, hub_entry,
        hass_client_no_auth) -> None:
    """B-093: at night the device is told to sleep 1 h; 2 h of silence is then not a miss.

    With the base rate (3 x 900 s) this turned on every night hour on 2026-11-08/09.
    """
    screen = hub_entry.runtime_data.screens["screen1"]
    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    with patch("custom_components.paperboard.views._refresh_rate", return_value=3600):
        assert (await dev.display())["refresh_rate"] == 3600
    assert screen.last_rate == 3600
    assert hass.states.get(ENTITY).attributes["allowed_seconds"] == 10800

    freezer.tick(timedelta(hours=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "off"

    freezer.tick(timedelta(hours=1, minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "on"


async def test_last_checkin_survives_a_restart(
        hass: HomeAssistant, freezer: FrozenDateTimeFactory, hub_entry,
        hass_client_no_auth) -> None:
    """B-093: after a reload the sensors still know when the device last polled."""
    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    await dev.display()
    before = hub_entry.runtime_data.screens["screen1"].last_checkin
    checkin_state = hass.states.get(CHECKIN).state

    assert await hass.config_entries.async_reload(hub_entry.entry_id)
    await hass.async_block_till_done()
    screen = hub_entry.runtime_data.screens["screen1"]
    assert screen.last_checkin == before
    assert hass.states.get(CHECKIN).state == checkin_state != "unknown"

    # The device never comes back: the alert counts from the stored check-in, not from the
    # restart, so it fires 2700 s after the last poll.
    freezer.tick(timedelta(seconds=2701))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "on"


async def test_stored_checkin_is_written_to_storage(hass: HomeAssistant, hub_entry,
                                                    hass_client_no_auth, hass_storage) -> None:
    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    await dev.display()
    await hub_entry.runtime_data.devices.async_flush()
    key = f"paperboard.{hub_entry.entry_id}.devices"
    saved = hass_storage[key]["data"]["screen1"]
    assert saved["last_checkin"] is not None and saved["last_rate"] == 900
