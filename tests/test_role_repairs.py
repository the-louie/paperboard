"""A bound entity that disappears raises a Repairs issue; it clears when it returns."""

from datetime import timedelta

from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

from custom_components.paperboard.const import DOMAIN, SUBENTRY_SCREEN
from custom_components.paperboard.role_watch import bound_entities
from tests.conftest import SCREEN_DATA


def test_bound_entities() -> None:
    roles = {"weather": "weather.a", "rooms": ["sensor.r1", "sensor.r2"], "price": ""}
    assert bound_entities(roles) == [("weather", "weather.a"), ("rooms[0]", "sensor.r1"),
                                     ("rooms[1]", "sensor.r2")]


async def test_missing_entity_issue(hass: HomeAssistant) -> None:
    assert await async_setup_component(hass, "http", {})
    hass.states.async_set("weather.home", "cloudy")
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={"refresh_rate": 900,
                 "roles": {"weather": "weather.home", "rooms": ["sensor.gone"]}},
        subentries_data=[ConfigSubentryData(data=SCREEN_DATA, subentry_type=SUBENTRY_SCREEN,
                                            title="Hallen", unique_id=None,
                                            subentry_id="screen1")])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    issues = ir.async_get(hass)
    assert issues.async_get_issue(DOMAIN, "role_missing_sensor_gone") is None  # grace period

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=121))
    await hass.async_block_till_done()
    issue = issues.async_get_issue(DOMAIN, "role_missing_sensor_gone")
    assert issue is not None and issue.translation_placeholders["role"] == "rooms[0]"
    assert issues.async_get_issue(DOMAIN, "role_missing_weather_home") is None

    hass.states.async_set("sensor.gone", "21")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()
    assert issues.async_get_issue(DOMAIN, "role_missing_sensor_gone") is None
