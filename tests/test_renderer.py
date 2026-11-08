"""Render scheduler: initial render, debounce, skip-unchanged, failure keeps last frame."""

import threading
from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import async_fire_time_changed

from custom_components.paperboard import layouts
from custom_components.paperboard.layouts import Layout, Snapshot, build_status
from custom_components.paperboard.text import Measurer

LOOP_THREADS: list[bool] = []


def _probe_build(snap: Snapshot, measure: Measurer) -> str:
    LOOP_THREADS.append(threading.current_thread() is threading.main_thread())
    if snap.states.get("sensor.probe", {}).get("state") == "explode":
        raise ValueError("layout bug")
    return build_status(snap, measure)


@pytest.fixture
def probe_layout(monkeypatch: pytest.MonkeyPatch) -> None:
    LOOP_THREADS.clear()
    monkeypatch.setitem(layouts.LAYOUTS, "status",
                        Layout(build=_probe_build, entities=("sensor.probe",),
                               clock_resolution=3600))


async def _settle(hass: HomeAssistant) -> None:
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_initial_render_off_the_loop(hass: HomeAssistant, probe_layout, hub_entry) -> None:
    renderer = hub_entry.runtime_data.renderers["screen1"]
    assert renderer.renders == 1
    assert hub_entry.runtime_data.screens["screen1"].frame is not None
    assert LOOP_THREADS == [False]  # drawn in an executor thread, not the event loop


async def test_burst_of_changes_renders_once(hass: HomeAssistant, probe_layout,
                                             hub_entry) -> None:
    renderer = hub_entry.runtime_data.renderers["screen1"]
    for value in ("1", "2", "3", "4"):
        hass.states.async_set("sensor.probe", value)
    await _settle(hass)
    assert renderer.renders == 1  # still waiting for the debounce cooldown
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await _settle(hass)
    assert renderer.renders == 2


async def test_tick_skips_unchanged_snapshot(hass: HomeAssistant, probe_layout,
                                             hub_entry) -> None:
    renderer = hub_entry.runtime_data.renderers["screen1"]
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await _settle(hass)
    assert renderer.renders == 1


async def test_layout_error_keeps_last_frame(hass: HomeAssistant, probe_layout,
                                             hub_entry) -> None:
    screen = hub_entry.runtime_data.screens["screen1"]
    good = screen.frame
    hass.states.async_set("sensor.probe", "explode")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await _settle(hass)
    assert screen.frame is good
    assert screen.stale is True
    assert "layout bug" in screen.last_error
