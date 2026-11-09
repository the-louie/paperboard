"""Generic image clients: token-in-path URL, BMP variant, ETag 304; the token stays out of
entity state (HACS review 2026-11-09)."""

from http import HTTPStatus

from homeassistant.core import HomeAssistant


async def test_paths_bmp_and_etag(hass: HomeAssistant, hub_entry, hass_client_no_auth) -> None:
    screen = hub_entry.runtime_data.screens["screen1"]
    base = f"/api/paperboard/image/screen1/{screen.image_token}/latest"
    client = await hass_client_no_auth()
    png = await client.get(f"{base}.png")
    assert png.status == HTTPStatus.OK and png.headers["Content-Type"] == "image/png"
    etag = png.headers["ETag"]
    assert (await client.get(f"{base}.png", headers={"If-None-Match": etag})).status == 304
    bmp = await client.get(f"{base}.bmp")
    body = await bmp.read()
    assert bmp.headers["Content-Type"] == "image/bmp" and len(body) == 48_062


async def test_token_not_in_any_state(hass: HomeAssistant, hub_entry) -> None:
    """State and attributes are visible to every user and kept in the recorder."""
    token = hub_entry.runtime_data.screens["screen1"].image_token
    for state in hass.states.async_all():
        assert token not in str(state.as_dict()), state.entity_id
