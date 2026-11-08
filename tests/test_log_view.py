"""/api/log stores recent entries per screen, only from the paired device."""

from homeassistant.core import HomeAssistant

from scripts.fake_trmnl import FakeTrmnl


async def test_log_from_paired_device(hass: HomeAssistant, hub_entry,
                                      hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    assert await dev.log("hello") == 204
    logs = hub_entry.runtime_data.screens["screen1"].logs
    assert logs[-1]["message"] == "hello"
    assert logs[-1]["firmware_version"] == "1.8.10"

    for i in range(60):
        await dev.log(f"line {i}")
    assert len(logs) == 50


async def test_log_rejected_without_key(hass: HomeAssistant, hub_entry,
                                        hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    assert await FakeTrmnl(client, api_key="nope").log("x") == 403
    resp = await client.post("/api/log", data=b"not json",
                             headers={"ID": "02:00:00:00:00:01", "Access-Token": ""})
    assert resp.status == 403
