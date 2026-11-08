"""Rotating the image token kills the old URL; the device keeps working."""

from http import HTTPStatus

from homeassistant.core import HomeAssistant

from scripts.fake_trmnl import FakeTrmnl


async def test_rotate_token(hass: HomeAssistant, hub_entry, hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    old_url = "/" + (await dev.display())["image_url"].split("/", 3)[3]
    assert (await client.get(old_url)).status == HTTPStatus.OK

    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_rotate_image_link"},
                                   blocking=True)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert (await client.get(old_url)).status == HTTPStatus.FORBIDDEN
    data = await dev.display()  # the paired device is unaffected
    assert data["status"] == 0
    new_url = "/" + data["image_url"].split("/", 3)[3]
    assert new_url != old_url and (await client.get(new_url)).status == HTTPStatus.OK
