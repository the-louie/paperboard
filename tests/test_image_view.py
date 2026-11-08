"""Token-in-path image URL: 200/304/403/404/503, HEAD, no gzip, stale flag."""

from http import HTTPStatus

from homeassistant.core import HomeAssistant

from custom_components.paperboard.pipeline import Frame
from custom_components.paperboard.views import image_path

PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 2000  # > 1 kB, so accidental compression would show


async def test_image_lifecycle(hass: HomeAssistant, hub_entry, hass_client_no_auth) -> None:
    screen = hub_entry.runtime_data.screens["screen1"]
    client = await hass_client_no_auth()
    base = f"/api/paperboard/image/screen1/{screen.image_token}/x.png"

    assert (await client.get(base)).status == HTTPStatus.SERVICE_UNAVAILABLE

    screen.set_frame(Frame(png=PNG, sha="abc123"))
    resp = await client.get(image_path(screen), headers={"Accept-Encoding": "gzip"})
    assert resp.status == HTTPStatus.OK
    assert resp.headers["ETag"] == '"abc123"'
    assert resp.headers.get("Content-Encoding") is None
    assert await resp.read() == PNG

    head = await client.head(base)
    assert head.status == HTTPStatus.OK
    assert head.headers["Content-Length"] == str(len(PNG))

    cached = await client.get(base, headers={"If-None-Match": '"abc123"'})
    assert cached.status == HTTPStatus.NOT_MODIFIED

    screen.render_failed("boom")
    assert (await client.get(base)).headers["X-Paperboard-Stale"] == "1"


async def test_wrong_token_and_unknown_screen(hass: HomeAssistant, hub_entry,
                                              hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    bad = await client.get("/api/paperboard/image/screen1/wrong/x.png")
    assert bad.status == HTTPStatus.FORBIDDEN
    missing = await client.get("/api/paperboard/image/nope/whatever/x.png")
    assert missing.status == HTTPStatus.NOT_FOUND
