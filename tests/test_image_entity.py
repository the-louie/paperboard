"""The image entity serves the current frame and updates when it changes."""

from http import HTTPStatus

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.paperboard.const import SIGNAL_FRAME
from custom_components.paperboard.pipeline import Frame

ENTITY = "image.hallen_screen_image"


async def test_image_entity(hass: HomeAssistant, hub_entry, hass_client) -> None:
    state = hass.states.get(ENTITY)
    assert state is not None
    before = state.state
    screen = hub_entry.runtime_data.screens["screen1"]
    screen.set_frame(Frame(png=b"\x89PNG one", sha="one"))
    async_dispatcher_send(hass, SIGNAL_FRAME.format("screen1"))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state != before

    client = await hass_client()
    resp = await client.get(f"/api/image_proxy/{ENTITY}")
    assert resp.status == HTTPStatus.OK
    assert await resp.read() == b"\x89PNG one"
