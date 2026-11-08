"""The emulated device behaves like the firmware on redirects, gzip and status 500."""

import json

import pytest
from aiohttp import web

from scripts.fake_trmnl import FakeTrmnl, FirmwareError

PNG = b"\x89PNG fake"


def _app(display_status: int = 0, image_redirect: int | None = None, gzip: bool = False):
    seen: dict = {}

    async def setup(req: web.Request) -> web.Response:
        seen["setup"] = dict(req.headers)
        return web.json_response({"status": 200, "api_key": "k", "friendly_id": "ABC123"})

    async def display(req: web.Request) -> web.Response:
        seen["display"] = dict(req.headers)
        return web.json_response({"status": display_status, "filename": "f1.png",
                                  "image_url": "/img/f1.png", "refresh_rate": 900})

    async def image(req: web.Request) -> web.StreamResponse:
        if image_redirect:
            return web.Response(status=image_redirect, headers={"Location": "/img2"})
        resp = web.Response(body=PNG, content_type="image/png")
        if gzip:
            resp.headers["Content-Encoding"] = "gzip"
        return resp

    async def image2(req: web.Request) -> web.Response:
        return web.Response(body=PNG, content_type="image/png")

    async def log(req: web.Request) -> web.Response:
        seen["log"] = json.loads(await req.read())
        return web.Response(status=204)

    app = web.Application()
    app.add_routes([web.get("/api/setup", setup), web.get("/api/display", display),
                    web.get("/img/f1.png", image), web.get("/img2", image2),
                    web.post("/api/log", log)])
    return app, seen


async def test_full_cycle_and_headers(socket_enabled, aiohttp_client) -> None:
    app, seen = _app()
    session = await aiohttp_client(app, auto_decompress=False)
    dev = FakeTrmnl(session)
    result = await dev.cycle()
    assert result["image"] == {"status": 200, "bytes": len(PNG)}
    assert "Access-Token" not in seen["setup"]
    for h in ("ID", "Access-Token", "Battery-Voltage", "FW-Version", "Model", "RSSI",
              "Refresh-Rate", "Image-Cached", "Width", "Height"):
        assert h in seen["display"], h
    assert seen["log"]["logs"][0]["message"] == "fake_trmnl cycle"
    again = await dev.cycle()
    assert "image" not in again  # cached filename: no download


@pytest.mark.parametrize(("code", "ok"), [(307, True), (308, True), (302, False)])
async def test_redirects(socket_enabled, aiohttp_client, code: int, ok: bool) -> None:
    app, _ = _app(image_redirect=code)
    session = await aiohttp_client(app, auto_decompress=False)
    dev = FakeTrmnl(session, api_key="k")
    if ok:
        assert await dev.fetch_image("/img/f1.png") == (200, PNG)
    else:
        with pytest.raises(FirmwareError):
            await dev.fetch_image("/img/f1.png")


async def test_gzip_refused_and_status_500_drops_key(socket_enabled, aiohttp_client) -> None:
    app, _ = _app(display_status=500, gzip=True)
    session = await aiohttp_client(app, auto_decompress=False)
    dev = FakeTrmnl(session, api_key="k")
    assert (await dev.display())["status"] == 500
    assert dev.api_key is None
    with pytest.raises(FirmwareError):
        await dev.fetch_image("/img/f1.png")
