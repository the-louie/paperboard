"""Shared fixtures: a set-up hub with one screen."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant.common import MockConfigEntry

from custom_components.paperboard.const import (
    CONF_IMAGE_TOKEN,
    CONF_LAYOUT,
    CONF_NAME,
    CONF_PROFILE,
    CONF_REFRESH_RATE,
    DOMAIN,
    SUBENTRY_SCREEN,
)

SCREEN_DATA = {CONF_NAME: "Hallen", CONF_PROFILE: "800x480_1bit", CONF_LAYOUT: "tidslinjen",
               CONF_REFRESH_RATE: 900, CONF_IMAGE_TOKEN: "img-token-for-tests-0123456789abcdef"}


@pytest.fixture
async def hub_entry(hass: HomeAssistant) -> MockConfigEntry:
    assert await async_setup_component(hass, "http", {})
    entry = MockConfigEntry(
        domain=DOMAIN, options={CONF_REFRESH_RATE: 900},
        subentries_data=[ConfigSubentryData(data=SCREEN_DATA, subentry_type=SUBENTRY_SCREEN,
                                            title="Hallen", unique_id=None,
                                            subentry_id="screen1")])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)  # initial render done
    return entry
