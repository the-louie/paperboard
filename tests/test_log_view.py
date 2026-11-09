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


async def _paired(hass: HomeAssistant, client) -> FakeTrmnl:
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    await dev.setup()
    return dev


async def test_chunked_body_over_limit_is_refused(hass: HomeAssistant, hub_entry,
                                                  hass_client_no_auth) -> None:
    """No Content-Length (chunked): the limit is enforced on the bytes actually read."""
    client = await hass_client_no_auth()
    dev = await _paired(hass, client)

    async def chunks():
        yield b'{"logs": [{"message": "'
        for _ in range(100):
            yield b"x" * 1024
        yield b'"}]}'

    resp = await client.post("/api/log", data=chunks(),
                             headers={"ID": dev.mac, "Access-Token": dev.api_key})
    assert resp.status == 413
    assert not hub_entry.runtime_data.screens["screen1"].logs


async def test_fields_are_cut_and_plain(hass: HomeAssistant, hub_entry,
                                        hass_client_no_auth) -> None:
    client = await hass_client_no_auth()
    dev = await _paired(hass, client)
    headers = {"ID": dev.mac, "Access-Token": dev.api_key}
    body = {"logs": [{"message": "y" * 10_000, "level": {"nested": 1}, "retry": 2}]}
    assert (await client.post("/api/log", json=body, headers=headers)).status == 204
    entry = hub_entry.runtime_data.screens["screen1"].logs[-1]
    assert entry == {"message": "y" * 500, "retry": 2}
    assert (await client.post("/api/log", json={"logs": {"a": 1}},
                              headers=headers)).status == 400
