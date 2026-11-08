"""The HA test harness loads paperboard as a custom integration."""

from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration


async def test_integration_is_discoverable(hass: HomeAssistant) -> None:
    integration = await async_get_integration(hass, "paperboard")
    assert integration.domain == "paperboard"
    assert integration.is_built_in is False
    assert integration.requirements == ["resvg-py==0.5.0"]
