"""/api/setup pairing window, driven by the emulated device."""

import time
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.pipeline import PanelProfile, render
from scripts.fake_trmnl import FakeTrmnl

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="480">'
       '<rect width="800" height="480" fill="#fff"/></svg>')


async def _press_pair(hass: HomeAssistant) -> None:
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)


async def test_setup_closed_by_default(hass: HomeAssistant, hub_entry,
                                       hass_client_no_auth) -> None:
    dev = FakeTrmnl(await hass_client_no_auth())
    assert (await dev.setup())["status"] == 404
    assert dev.api_key is None


async def test_pairing_window_pairs_once(hass: HomeAssistant, hub_entry,
                                         hass_client_no_auth) -> None:
    hub = hub_entry.runtime_data
    hub.screens["screen1"].set_frame(render(SVG, PanelProfile(), FONT_DIR))
    client = await hass_client_no_auth()
    await _press_pair(hass)

    dev = FakeTrmnl(client, mac="02:00:00:00:00:aa")
    data = await dev.setup()
    assert data["status"] == 200
    assert len(dev.api_key) >= 40
    assert data["friendly_id"] == dev.friendly_id and len(dev.friendly_id) == 6
    assert hub.devices.devices["screen1"].mac == "02:00:00:00:00:AA"

    path = "/" + data["image_url"].split("/", 3)[3]  # absolute URL -> test-client path
    status, bmp = await dev.fetch_image(path)
    assert status == 200 and len(bmp) == 48_062

    other = FakeTrmnl(client, mac="02:00:00:00:00:bb")
    assert (await other.setup())["status"] == 404  # window closed after one pairing


async def test_pairing_window_expires(hass: HomeAssistant, hub_entry,
                                      hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    await _press_pair(hass)
    with patch("custom_components.paperboard.runtime.time.monotonic",
               return_value=time.monotonic() + 301):
        assert (await FakeTrmnl(client).setup())["status"] == 404


async def test_deleted_screen_forgets_device(hass: HomeAssistant, hub_entry,
                                             hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    await _press_pair(hass)
    await FakeTrmnl(client).setup()
    hass.config_entries.async_remove_subentry(hub_entry, "screen1")
    await hass.async_block_till_done()
    assert not hub_entry.runtime_data.devices.devices


async def test_pairing_refused_from_outside_lan(hass: HomeAssistant, hub_entry,
                                                hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    await _press_pair(hass)
    with patch("custom_components.paperboard.views.is_local", return_value=False):
        data = await FakeTrmnl(client).setup()
    assert data["status"] == 404
    assert "local network" in data["message"]
    assert hub_entry.runtime_data.pairing_target() == "screen1"  # window still open for the LAN
    with patch("custom_components.paperboard.views.is_cloud_connection", return_value=True):
        assert (await FakeTrmnl(client).setup())["status"] == 404
    assert (await FakeTrmnl(client).setup())["status"] == 200


async def test_known_device_repairs_without_window(hass: HomeAssistant, hub_entry,
                                                   hass_client_no_auth) -> None:
    """B-094: a factory-reset panel the hub already knows pairs again with no button press."""
    hub = hub_entry.runtime_data
    client = await hass_client_no_auth()
    await _press_pair(hass)
    dev = FakeTrmnl(client, mac="02:00:00:00:00:aa")
    first = await dev.setup()
    assert hub.pairing_target() is None

    again = FakeTrmnl(client, mac="02:00:00:00:00:aa")  # same panel, key wiped
    data = await again.setup()
    assert data["status"] == 200
    assert data["api_key"] != first["api_key"]  # the old key is revoked
    assert hub.devices.devices["screen1"].api_key == data["api_key"]

    assert (await FakeTrmnl(client, mac="02:00:00:00:00:bb").setup())["status"] == 404
    with patch("custom_components.paperboard.views.is_local", return_value=False):
        assert (await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup())["status"] == 404


async def test_open_window_beats_known_device(hass: HomeAssistant, hub_entry,
                                              hass_client_no_auth) -> None:
    """A known panel that sets up while a window is open still closes that window."""
    client = await hass_client_no_auth()
    await _press_pair(hass)
    await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup()
    await _press_pair(hass)
    assert (await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup())["status"] == 200
    assert hub_entry.runtime_data.pairing_target() is None
