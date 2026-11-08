"""Profile 'auto' follows the device: the owner's XIAO stays 800x480 1-bit, a TRMNL X switches."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant.common import MockConfigEntry

from custom_components.paperboard.const import CONF_PROFILE, DOMAIN, SUBENTRY_SCREEN
from scripts import fake_trmnl
from scripts.fake_trmnl import FakeTrmnl
from tests.conftest import SCREEN_DATA


async def _entry(hass: HomeAssistant) -> MockConfigEntry:
    assert await async_setup_component(hass, "http", {})
    entry = MockConfigEntry(domain=DOMAIN, options={"refresh_rate": 900}, subentries_data=[
        ConfigSubentryData(data={**SCREEN_DATA, CONF_PROFILE: "auto"},
                           subentry_type=SUBENTRY_SCREEN, title="Hallen", unique_id=None,
                           subentry_id="screen1")])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    return entry


async def _checkin(hass: HomeAssistant, client, model: str, w: str, h: str) -> None:
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    with patch.object(fake_trmnl, "MODEL", model):
        await dev.setup()
        headers = dev.display_headers() | {"Width": w, "Height": h}
        await client.get("/api/display", headers=headers)
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_owner_xiao_stays_og(hass: HomeAssistant, hass_client_no_auth) -> None:
    entry = await _entry(hass)
    await _checkin(hass, await hass_client_no_auth(), "xiao_epaper_display", "800", "480")
    p = entry.runtime_data.renderers["screen1"].profile
    assert (p.width, p.height, p.bit_depth) == (800, 480, 1)


async def test_trmnl_x_switches_profile(hass: HomeAssistant, hass_client_no_auth) -> None:
    entry = await _entry(hass)
    await _checkin(hass, await hass_client_no_auth(), "v2", "1872", "1404")
    renderer = entry.runtime_data.renderers["screen1"]
    assert (renderer.profile.width, renderer.profile.height) == (1872, 1404)
    frame = entry.runtime_data.screens["screen1"].frame
    assert frame is not None
