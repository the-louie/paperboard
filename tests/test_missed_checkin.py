"""Missed check-in turns on after 3 x refresh rate without a poll, off again on a poll."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import async_fire_time_changed

from scripts.fake_trmnl import FakeTrmnl

ENTITY = "binary_sensor.hallen_missed_check_in"


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
