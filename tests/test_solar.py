"""Solar provider: energy platform of the bound sensor's integration, fallbacks."""

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.paperboard.data import SolarProvider


async def _bind(hass: HomeAssistant, platform: str = "forecast_solar") -> str:
    entry = MockConfigEntry(domain=platform)
    entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create("sensor", platform, "today", config_entry=entry,
                                           suggested_object_id="energy_production_today")
    hass.states.async_set("sensor.energy_production_today", "3.657",
                          {"unit_of_measurement": "kWh"})
    return entry.entry_id


async def test_energy_platform_curve(hass: HomeAssistant) -> None:
    entry_id = await _bind(hass)
    seen = {}

    async def forecast(_hass, config_entry_id):
        seen["entry"] = config_entry_id
        return {"wh_hours": {"2026-11-08T11:00:00+00:00": 900, "2026-11-08T12:00:00+00:00": 700}}

    module = SimpleNamespace(async_get_solar_forecast=forecast)
    integration = SimpleNamespace(async_get_platform=lambda _n: _async(module))
    with patch("custom_components.paperboard.data.async_get_integration",
               return_value=integration):
        provider = SolarProvider(hass, "sensor.energy_production_today")
        await provider.async_refresh()
    snap = provider.snapshot()
    assert seen["entry"] == entry_id
    assert [wh for _s, wh in snap.hours] == [900.0, 700.0]
    assert snap.today_kwh == 3.657  # the sensor's own total wins


async def test_no_energy_platform_falls_back_to_total(hass: HomeAssistant) -> None:
    await _bind(hass, platform="some_sensor")
    provider = SolarProvider(hass, "sensor.energy_production_today")
    await provider.async_refresh()
    snap = provider.snapshot()
    assert snap.hours == [] and snap.today_kwh == 3.657


async def test_unbound(hass: HomeAssistant) -> None:
    provider = SolarProvider(hass, None)
    await provider.async_refresh()
    assert provider.snapshot().hours == [] and provider.snapshot().today_kwh is None


async def _async(value):
    return value
