"""Hub config flow and options flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

from custom_components.paperboard.const import CONF_BASE_URL, CONF_REFRESH_RATE, DOMAIN


async def test_user_flow_creates_hub(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BASE_URL: "http://10.0.0.5:8123/", CONF_REFRESH_RATE: 600})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {CONF_BASE_URL: "http://10.0.0.5:8123", CONF_REFRESH_RATE: 600}


async def test_single_instance(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, options={CONF_REFRESH_RATE: 900}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_updates_and_reloads(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, options={CONF_BASE_URL: "", CONF_REFRESH_RATE: 900})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_BASE_URL: "", CONF_REFRESH_RATE: 300})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options[CONF_REFRESH_RATE] == 300
