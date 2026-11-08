"""A broken layout file raises a Repairs issue; fixing it clears the issue."""

from datetime import timedelta
from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import async_fire_time_changed

from tests.test_layout_file import GOOD


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Writable per-test config dir (the shared testing_config is read-only by design)."""
    return hass_tmp_config_dir


async def test_bad_layout_raises_and_clears_issue(hass: HomeAssistant, hub_entry) -> None:
    user_dir = Path(hass.config.path("paperboard"))
    user_dir.mkdir(exist_ok=True)
    path = user_dir / "mine.yaml"
    try:
        path.write_text(GOOD.replace("type: now", "type: clock"))
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
        await hass.async_block_till_done(wait_background_tasks=True)
        issue = ir.async_get(hass).async_get_issue("paperboard", "layout_mine")
        assert issue is not None
        assert "widgets[1].type" in issue.translation_placeholders["errors"]

        path.write_text(GOOD)
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=62))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert ir.async_get(hass).async_get_issue("paperboard", "layout_mine") is None
        assert "demo" in hub_entry.runtime_data.layouts.result.layouts
    finally:
        path.unlink(missing_ok=True)
