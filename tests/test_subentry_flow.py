"""Screen subentries: add, reconfigure, delete -> device registry follows."""

import json
from pathlib import Path

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

SCREEN = {CONF_NAME: "Hallen", CONF_PROFILE: "auto", CONF_LAYOUT: "tidslinjen",
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


def _layout_selector(result: dict):
    for key, selector in result["data_schema"].schema.items():
        if str(key) == CONF_LAYOUT:
            return selector
    raise AssertionError("no layout field")


async def test_layout_is_a_dropdown_with_bundled_and_own_files(hass: HomeAssistant,
                                                               tmp_path: Path) -> None:
    """Owner 2026-11-09: layout as a dropdown of the bundled layouts, plus free text."""
    hass.config.config_dir = str(tmp_path)
    own = Path(hass.config.path(DOMAIN))
    own.mkdir()
    (own / "hallen.yaml").write_text(
        'name: hallen\ndefault: tidslinjen\nschedule:\n'
        '  - {layout: tavlan, from: "06:30", to: "08:00"}\n', encoding="utf-8")
    entry = await _hub(hass)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_SCREEN), context={"source": SOURCE_USER})
    config = _layout_selector(result).config
    assert config["custom_value"] is True
    values = [o["value"] for o in config["options"]]
    labels = {o["value"]: o["label"] for o in config["options"]}
    bundled = {"almanackan", "bento", "energi", "tavlan", "tidningen", "tidslinjen", "trmnl"}
    assert bundled <= set(values)
    assert values[-1] == "hallen"  # own files after the bundled ones
    assert labels["hallen"] == "hallen (your schedule file)"
    assert labels["tavlan"] == "tavlan (bundled)"
    # Free text is still accepted (a file added a second ago).
    done = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**SCREEN, CONF_LAYOUT: "not_yet_written"})
    assert done["type"] is FlowResultType.CREATE_ENTRY


def test_every_role_has_a_description_in_every_language() -> None:
    """Owner 2026-11-09: each role explains what kind of value it expects."""
    base = Path(__file__).parent.parent / "custom_components" / "paperboard"
    for path in (base / "strings.json", *sorted((base / "translations").glob("*.json"))):
        roles = json.loads(path.read_text(encoding="utf-8"))["options"]["step"]["roles"]
        missing = set(roles["data"]) - set(roles.get("data_description", {}))
        assert not missing, f"{path.name}: no description for {sorted(missing)}"
        assert all(len(t) > 20 for t in roles["data_description"].values()), path.name
