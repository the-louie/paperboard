"""Screen subentries: add, reconfigure, delete -> device registry follows."""

from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant.common import MockConfigEntry

from custom_components.paperboard.const import (
    CONF_LAYOUT,
    CONF_MAC,
    CONF_NAME,
    CONF_PROFILE,
    CONF_REFRESH_RATE,
    DOMAIN,
    SUBENTRY_SCREEN,
)

SCREEN = {CONF_NAME: "Hallen", CONF_PROFILE: "800x480_1bit", CONF_LAYOUT: "tidslinjen",
          CONF_REFRESH_RATE: 900}


async def _hub(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, options={CONF_REFRESH_RATE: 600})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    return entry


async def _add_screen(hass: HomeAssistant, entry: MockConfigEntry, data: dict) -> dict:
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_SCREEN), context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.subentries.async_configure(result["flow_id"], data)


async def test_add_screen_creates_device(hass: HomeAssistant) -> None:
    entry = await _hub(hass)
    result = await _add_screen(hass, entry, SCREEN)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done(wait_background_tasks=True)
    (subentry,) = entry.subentries.values()
    assert subentry.title == "Hallen"
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert [d.name for d in devices] == ["Hallen"]
    assert devices[0].config_entry_id == entry.entry_id
    assert devices[0].config_subentry_id == subentry.subentry_id


async def test_blank_name_rejected(hass: HomeAssistant) -> None:
    entry = await _hub(hass)
    result = await _add_screen(hass, entry, {**SCREEN, CONF_NAME: "  "})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_NAME: "name_required"}


async def test_reconfigure_keeps_pairing_data(hass: HomeAssistant) -> None:
    entry = await _hub(hass)
    await _add_screen(hass, entry, SCREEN)
    await hass.async_block_till_done(wait_background_tasks=True)
    (subentry,) = entry.subentries.values()
    hass.config_entries.async_update_subentry(entry, subentry,
                                              data={**subentry.data, CONF_MAC: "AA:BB"})
    await hass.async_block_till_done(wait_background_tasks=True)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_SCREEN),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id})
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**SCREEN, CONF_NAME: "Köket", CONF_REFRESH_RATE: 300})
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done(wait_background_tasks=True)  # let the reload finish
    updated = entry.subentries[subentry.subentry_id]
    assert updated.title == "Köket"
    assert updated.data[CONF_MAC] == "AA:BB"
    assert updated.data[CONF_REFRESH_RATE] == 300


async def test_delete_screen_removes_device(hass: HomeAssistant) -> None:
    entry = await _hub(hass)
    await _add_screen(hass, entry, SCREEN)
    await hass.async_block_till_done(wait_background_tasks=True)
    (subentry,) = entry.subentries.values()
    hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert not dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
