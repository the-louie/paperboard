"""Pin the HA HTTP behaviour that the TRMNL device API relies on (T-03).

If an HA upgrade changes any of this, these tests fail before devices do.
"""

from http import HTTPStatus

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


class _Probe(HomeAssistantView):
    """Stands in for /api/display: unauthenticated, checks its own token."""

    url = "/api/display"
    name = "api:paperboard:probe"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        if request.headers.get("Access-Token") != "good":
            # Returned, not raised: a raised HTTPUnauthorized feeds HA's ip_ban counter.
            return web.Response(status=HTTPStatus.FORBIDDEN)
        return web.Response(body=b'{"status":0}', content_type="application/json")


async def test_unauthenticated_view_under_api(hass: HomeAssistant, hass_client_no_auth) -> None:
    http_conf = {"ip_ban_enabled": True, "login_attempts_threshold": 2}
    assert await async_setup_component(hass, "http", {"http": http_conf})
    hass.http.register_view(_Probe())
    client = await hass_client_no_auth()

    ok = await client.get("/api/display", headers={"Access-Token": "good"})
    assert ok.status == HTTPStatus.OK
    assert ok.headers.get("Content-Encoding") is None

    for _ in range(5):
        bad = await client.get("/api/display", headers={"Access-Token": "bad"})
        assert bad.status == HTTPStatus.FORBIDDEN
    # A returned 403 is not a failed login: with threshold 2, five counted failures would
    # have banned the client and turned this request into a 403.
    again = await client.get("/api/display", headers={"Access-Token": "good"})
    assert again.status == HTTPStatus.OK


async def test_core_has_no_conflicting_routes(hass: HomeAssistant) -> None:
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, "api", {})
    paths = {r.resource.canonical for r in hass.http.app.router.routes() if r.resource}
    for path in ("/api/setup", "/api/display", "/api/log"):
        assert path not in paths, path
