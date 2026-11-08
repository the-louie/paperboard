"""Diagnostics carry the debugging facts and none of the secrets."""

import json

from homeassistant.core import HomeAssistant
from pytest_homeassistant.components.diagnostics import get_diagnostics_for_config_entry

from scripts.fake_trmnl import FakeTrmnl


async def test_diagnostics_redacted(hass: HomeAssistant, hub_entry, hass_client,
                                    hass_client_no_auth) -> None:
    dev_client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(dev_client, mac="02:00:00:00:12:34")
    await dev.setup()
    await dev.display()
    await dev.log("hi")
    await FakeTrmnl(dev_client, mac="02:00:00:00:99:99", api_key="bad").display()

    diag = await get_diagnostics_for_config_entry(hass, hass_client, hub_entry)
    screen = diag["screens"]["screen1"]
    assert screen["paired_device"] == "**:**:**:**:12:34"
    assert screen["frame"]["bytes"] > 0
    assert screen["telemetry"]["FW-Version"] == "1.8.10"
    assert screen["device_logs"][-1]["message"] == "hi"
    assert diag["last_rejected"]["mac"] == "**:**:**:**:99:99"
    blob = json.dumps(diag)
    for secret in (dev.api_key, hub_entry.runtime_data.screens["screen1"].image_token,
                   "02:00:00:00:12:34"):
        assert secret not in blob
