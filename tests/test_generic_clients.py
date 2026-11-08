"""Generic image clients: attributes expose the paths, BMP variant, ETag 304."""

from http import HTTPStatus

from homeassistant.core import HomeAssistant


async def test_paths_bmp_and_etag(hass: HomeAssistant, hub_entry, hass_client_no_auth) -> None:
    attrs = hass.states.get("image.hallen_screen_image").attributes
    client = await hass_client_no_auth()
    png = await client.get(attrs["png_path"])
    assert png.status == HTTPStatus.OK and png.headers["Content-Type"] == "image/png"
    etag = png.headers["ETag"]
    assert (await client.get(attrs["png_path"], headers={"If-None-Match": etag})).status == 304
    bmp = await client.get(attrs["bmp_path"])
    body = await bmp.read()
    assert bmp.headers["Content-Type"] == "image/bmp" and len(body) == 48_062
