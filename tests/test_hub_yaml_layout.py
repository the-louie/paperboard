"""End to end in HA: a screen on the bundled tidslinjen layout renders through roles."""

from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant.common import MockConfigEntry

from custom_components.paperboard.const import CONF_LAYOUT, DOMAIN, SUBENTRY_SCREEN
from tests.conftest import SCREEN_DATA


async def test_tidslinjen_live(hass: HomeAssistant) -> None:
    assert await async_setup_component(hass, "http", {})
    hass.states.async_set("weather.home", "cloudy", {"temperature": 3.2, "humidity": 91,
                                                     "wind_speed": 5.4,
                                                     "wind_speed_unit": "km/h"})
    hass.states.async_set("sensor.price", "1.93", {
        "unit_of_measurement": "SEK/kWh",
        "raw_today": [{"start": f"2026-11-08T{h:02d}:00:00+01:00",
                       "end": f"2026-11-08T{h:02d}:59:59+01:00", "value": 1.5 + h / 20}
                      for h in range(24)]})
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={"refresh_rate": 900, "roles": {"weather": "weather.home",
                                                "price": "sensor.price"}},
        subentries_data=[ConfigSubentryData(data={**SCREEN_DATA, CONF_LAYOUT: "tidslinjen"},
                                            subentry_type=SUBENTRY_SCREEN, title="Hallen",
                                            unique_id=None, subentry_id="screen1")])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    screen = entry.runtime_data.screens["screen1"]
    assert screen.frame is not None and screen.last_error is None
    assert 0 < len(screen.frame.png) < 90_000
    assert "weather.home" in entry.runtime_data.renderers["screen1"].entities
