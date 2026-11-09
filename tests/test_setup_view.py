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


async def test_known_device_needs_the_window(hass: HomeAssistant, hub_entry,
                                            hass_client_no_auth) -> None:
    """A paired MAC proves nothing (every LAN device sees it): re-pairing needs the window too,
    so a spoofer cannot take a key and lock the real panel out (HACS review 2026-11-09)."""
    hub = hub_entry.runtime_data
    client = await hass_client_no_auth()
    await _press_pair(hass)
    first = await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup()
    assert first["status"] == 200 and hub.pairing_target() is None

    spoof = await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup()
    assert spoof["status"] == 404 and "api_key" not in spoof
    assert hub.devices.devices["screen1"].api_key == first["api_key"]  # the real panel keeps it

    await _press_pair(hass)  # the owner re-pairs after a factory reset
    again = await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup()
    assert again["status"] == 200 and again["api_key"] != first["api_key"]
    assert hub.devices.devices["screen1"].api_key == again["api_key"]


async def test_open_window_beats_known_device(hass: HomeAssistant, hub_entry,
                                              hass_client_no_auth) -> None:
    """A known panel that sets up while a window is open still closes that window."""
    client = await hass_client_no_auth()
    await _press_pair(hass)
    await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup()
    await _press_pair(hass)
    assert (await FakeTrmnl(client, mac="02:00:00:00:00:aa").setup())["status"] == 200
    assert hub_entry.runtime_data.pairing_target() is None


async def test_long_id_is_capped_and_still_authenticates(hass: HomeAssistant, hub_entry,
                                                         hass_client_no_auth) -> None:
    """An ID header is stored at most 64 characters long; the same long ID still polls."""
    client = await hass_client_no_auth()
    await _press_pair(hass)
    dev = FakeTrmnl(client, mac="x" * 100)
    assert (await dev.setup())["status"] == 200
    assert hub_entry.runtime_data.devices.devices["screen1"].mac == "X" * 64
    assert (await dev.display())["status"] in (0, 202)


async def _setup_with(client, headers: dict[str, str]) -> dict:
    resp = await client.get("/api/setup", headers={"ID": "02:00:00:00:00:cc", **headers})
    return await resp.json()


async def test_proxy_naming_an_outside_client_cannot_pair(hass: HomeAssistant, hub_entry,
                                                          hass_client_no_auth) -> None:
    """A proxy HA is not configured for hides the caller behind its own LAN address; the
    client address it forwards must be local too."""
    client = await hass_client_no_auth()
    await _press_pair(hass)
    for headers in ({"X-Real-IP": "203.0.113.7"},
                    {"CF-Connecting-IP": "203.0.113.7"},
                    {"True-Client-IP": "2001:db8::7"},
                    {"Forwarded": 'for=203.0.113.7;proto=https'},
                    {"Forwarded": 'for="[2001:db8::7]:443"'},
                    {"Forwarded": "for=_hidden"}):
        data = await _setup_with(client, headers)
        assert data["status"] == 404 and "local network" in data["message"], headers
    assert hub_entry.runtime_data.pairing_target() == "screen1"  # still open for the panel


async def test_proxy_naming_a_lan_client_still_pairs(hass: HomeAssistant, hub_entry,
                                                     hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    await _press_pair(hass)
    assert (await _setup_with(client, {"X-Real-IP": "192.168.1.50:4321"}))["status"] == 200
    await _press_pair(hass)
    assert (await _setup_with(client, {"Forwarded": "for=10.0.0.5"}))["status"] == 200


async def test_pairing_is_announced(hass: HomeAssistant, hub_entry, hass_client_no_auth) -> None:
    """Every pairing shows the panel's code, so a device that took the window is noticed."""
    from homeassistant.components import persistent_notification

    client = await hass_client_no_auth()
    await _press_pair(hass)
    dev = FakeTrmnl(client, mac="02:00:00:00:00:aa")
    await dev.setup()
    notes = persistent_notification._async_get_or_create_notifications(hass)
    note = notes["paperboard_paired_screen1"]
    assert dev.friendly_id in note["message"] and "00:AA" in note["message"]
    assert dev.api_key not in note["message"]
