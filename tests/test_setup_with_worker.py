"""Regression, 2026-11-08 live: setup with the render worker on, and a device polling while
the hub is not loaded."""

from custom_components.paperboard import pipeline, raster_worker


async def test_setup_starts_the_worker_warm_up(hass, monkeypatch) -> None:
    """async_add_executor_job returns a Future; wrapping it in a background task raised
    TypeError and failed the whole entry on ha-host (HA 2026.11.0)."""
    calls = []
    monkeypatch.setattr(pipeline, "USE_WORKER", True)
    monkeypatch.setattr(raster_worker.WORKER, "render",
                        lambda svg, font_dir: calls.append(svg) or b"")
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant.common import MockConfigEntry

    from custom_components.paperboard.const import DOMAIN

    assert await async_setup_component(hass, "http", {})
    entry = MockConfigEntry(domain=DOMAIN, options={"refresh_rate": 900})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.state is ConfigEntryState.LOADED
    assert calls  # the warm-up ran


async def test_display_while_not_loaded_keeps_the_device_key(
        hass, hub_entry, hass_client_no_auth, socket_enabled) -> None:
    """A 500 makes the firmware drop its key and need pairing again: never while unloaded."""
    client = await hass_client_no_auth()
    assert await hass.config_entries.async_unload(hub_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    resp = await client.get("/api/display", headers={"ID": "02:00:00:00:00:01",
                                                     "Access-Token": "whatever"})
    data = await resp.json(content_type=None)
    assert data["status"] == 202 and data["refresh_rate"] == 60
