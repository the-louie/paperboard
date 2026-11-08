"""Forecast cache: both types fetched, unsupported types tolerated, no weather = no-op."""

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError

from custom_components.paperboard.data import ForecastCache


async def _register(hass: HomeAssistant, hourly_ok: bool = True) -> list[str]:
    calls: list[str] = []

    async def handler(call: ServiceCall):
        calls.append(call.data["type"])
        if call.data["type"] == "hourly" and not hourly_ok:
            raise ServiceValidationError("unsupported")
        return {call.data["entity_id"]: {"forecast": [{"datetime": "2026-11-08T12:00:00+00:00",
                                                        "temperature": 4.0}]}}

    hass.services.async_register("weather", "get_forecasts", handler,
                                 supports_response=SupportsResponse.ONLY)
    return calls


async def test_both_types(hass: HomeAssistant) -> None:
    calls = await _register(hass)
    cache = ForecastCache(hass, "weather.home")
    await cache.async_refresh()
    assert calls == ["hourly", "daily"]
    assert cache.forecasts["daily"][0]["temperature"] == 4.0
    assert cache.fetched is not None


async def test_unsupported_type_is_just_missing(hass: HomeAssistant) -> None:
    await _register(hass, hourly_ok=False)
    cache = ForecastCache(hass, "weather.home")
    await cache.async_refresh()
    assert "hourly" not in cache.forecasts
    assert cache.forecasts["daily"]


async def test_no_weather_role(hass: HomeAssistant) -> None:
    cache = ForecastCache(hass, None)
    await cache.async_refresh()
    assert cache.forecasts == {}
    cache.async_start()()


async def test_service_missing(hass: HomeAssistant) -> None:
    cache = ForecastCache(hass, "weather.home")
    await cache.async_refresh()  # weather integration not loaded: ServiceNotFound
    assert cache.forecasts == {}
