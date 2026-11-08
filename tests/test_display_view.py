"""/api/display auth matrix and response, driven by the emulated device."""

from homeassistant.core import HomeAssistant

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.pipeline import PanelProfile, render
from scripts.fake_trmnl import FakeTrmnl

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="480">'
       '<rect width="800" height="480" fill="#fff"/>'
       '<text x="20" y="40" font-family="TRMNL16" font-size="16">x</text></svg>')


async def _paired(hass: HomeAssistant, client) -> FakeTrmnl:
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client, mac="02:00:00:00:00:aa")
    assert (await dev.setup())["status"] == 200
    return dev


async def test_display_ok_with_telemetry(hass: HomeAssistant, hub_entry,
                                         hass_client_no_auth) -> None:
    screen = hub_entry.runtime_data.screens["screen1"]
    client = await hass_client_no_auth()
    dev = await _paired(hass, client)

    screen.frame = None  # as before the first render
    assert (await dev.display())["status"] == 202

    frame = render(SVG, PanelProfile(), FONT_DIR)
    screen.set_frame(frame)
    data = await dev.display()
    assert data["status"] == 0
    assert data["filename"] == frame.sha
    assert data["refresh_rate"] == 900
    assert data["image_url"].endswith(f"/{frame.sha}.png")
    assert "reset_firmware" in data and data["reset_firmware"] is False
    assert screen.telemetry["Battery-Voltage"] == "4.20"
    assert screen.telemetry["FW-Version"] == "1.8.10"
    assert "Access-Token" not in screen.telemetry
    assert screen.last_checkin is not None


async def test_full_cycle_downloads_once(hass: HomeAssistant, hub_entry,
                                         hass_client_no_auth) -> None:
    hub_entry.runtime_data.screens["screen1"].set_frame(render(SVG, PanelProfile(), FONT_DIR))
    client = await hass_client_no_auth()
    dev = await _paired(hass, client)
    dev.base = ""
    first = await dev.cycle_relative()
    assert first["image"]["status"] == 200
    second = await dev.cycle_relative()
    assert "image" not in second  # same filename -> device keeps its cached image


async def test_bad_token_and_unknown_device(hass: HomeAssistant, hub_entry,
                                            hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    dev = await _paired(hass, client)
    dev.api_key = "wrong"
    data = await dev.display()
    assert data == {"status": 500, "message": "Unknown device, re-running setup"}
    assert dev.api_key is None
    stranger = FakeTrmnl(client, mac="02:00:00:00:00:ff", api_key="x")
    assert (await stranger.display())["status"] == 500
    assert hub_entry.runtime_data.last_rejected["mac"] == "02:00:00:00:00:FF"
