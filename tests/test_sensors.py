"""Telemetry sensors follow the device's check-ins."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.paperboard.runtime import battery_percent
from scripts.fake_trmnl import FakeTrmnl


@pytest.mark.parametrize(("volts", "pct"), [(4.3, 100), (4.2, 100), (3.95, 70), (3.3, 0),
                                            (3.0, 0)])
def test_battery_curve(volts: float, pct: int) -> None:
    assert battery_percent(volts) == pct


async def test_sensors_update_on_checkin(hass: HomeAssistant, hub_entry,
                                         hass_client_no_auth) -> None:
    assert hass.states.get("sensor.hallen_battery").state == "unknown"
    client = await hass_client_no_auth()
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client, battery_v="3.95", rssi="-61")
    await dev.setup()
    await dev.display()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.hallen_battery").state == "70"
    assert hass.states.get("sensor.hallen_battery_voltage").state == "3.95"
    assert hass.states.get("sensor.hallen_wi_fi_signal").state == "-61.0"
    assert hass.states.get("sensor.hallen_firmware").state == "1.8.10"
    assert hass.states.get("sensor.hallen_last_check_in").state not in ("unknown", "")
    assert hass.states.get("sensor.hallen_render_error").state == "none"
