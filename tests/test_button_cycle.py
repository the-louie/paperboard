"""B-089: the device button steps through layouts; a double click returns to the schedule."""

import datetime as dt

import pytest
from homeassistant.util import dt as dt_util

from custom_components.paperboard.renderer import DEFAULT_CYCLE, HOLD_MINUTES
from custom_components.paperboard.schedule import parse_schedule
from scripts.fake_trmnl import FakeTrmnl


async def _paired(hass, client, entry) -> FakeTrmnl:
    await hass.services.async_call("button", "press",
                                   {"entity_id": "button.hallen_pair_device"}, blocking=True)
    dev = FakeTrmnl(client)
    assert (await dev.setup())["status"] == 200
    return dev


async def _wake(dev: FakeTrmnl, source: str, special: str | None = None) -> dict:
    headers = {**dev.display_headers(), "Update-Source": source}
    if special:
        headers["special_function"] = special
    resp = await dev.session.get("/api/display", headers=headers)
    return await resp.json(content_type=None)


async def test_short_press_steps_and_double_click_resumes(
        hass, hub_entry, hass_client_no_auth, socket_enabled) -> None:
    client = await hass_client_no_auth()
    dev = await _paired(hass, client, hub_entry)
    renderer = hub_entry.runtime_data.renderers["screen1"]
    assert list(renderer.cycle) == list(DEFAULT_CYCLE)  # all 7 bundled layouts

    base = await _wake(dev, "timer")
    first = await _wake(dev, "button")
    assert renderer.held[0] == DEFAULT_CYCLE[0]  # "status" is not in the cycle: start at 0
    assert first["filename"] != base["filename"]  # rendered before answering
    assert first["refresh_rate"] <= HOLD_MINUTES * 60 + 30

    second = await _wake(dev, "button")
    assert renderer.held[0] == DEFAULT_CYCLE[1]
    assert second["filename"] != first["filename"]

    back = await _wake(dev, "button", special="true")
    assert renderer.held is None
    assert back["filename"] == base["filename"]

    timer = await _wake(dev, "timer")  # a timer wake never steps
    assert renderer.held is None and timer["filename"] == base["filename"]
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_cycle_wraps_and_hold_expires(hass, hub_entry) -> None:
    renderer = hub_entry.runtime_data.renderers["screen1"]
    for _ in range(len(DEFAULT_CYCLE)):
        await renderer.async_step()
    assert renderer.held[0] == DEFAULT_CYCLE[-1]
    await renderer.async_step()
    assert renderer.held[0] == DEFAULT_CYCLE[0]  # wraps
    renderer.held = (renderer.held[0], dt_util.now() - dt.timedelta(seconds=1))
    assert renderer.held_layout(dt_util.now()) is None
    assert renderer.shown_name(dt_util.now()) == "status"
    await hass.async_block_till_done(wait_background_tasks=True)


def test_schedule_cycle_keys() -> None:
    raw = {"name": "hallen", "default": "tidslinjen", "schedule": [{"layout": "tavlan"}],
           "cycle": ["tidslinjen", "energi"], "hold_minutes": 10}
    spec = parse_schedule(raw, "x")
    assert spec.cycle == ("tidslinjen", "energi") and spec.hold_minutes == 10
    plain = {k: v for k, v in raw.items() if k not in ("cycle", "hold_minutes")}
    assert parse_schedule(plain, "x").cycle is None


@pytest.mark.parametrize("bad", [{"cycle": []}, {"hold_minutes": 0}, {"cycle": "tavlan"}])
def test_schedule_cycle_validation(bad) -> None:
    raw = {"name": "h", "default": "tidslinjen", "schedule": [{"layout": "tavlan"}], **bad}
    with pytest.raises(Exception):  # noqa: B017 - the schema shim raises its own Invalid
        parse_schedule(raw, "x")


def test_unknown_cycle_layout_rejects_the_schedule(tmp_path, monkeypatch) -> None:
    from custom_components.paperboard import layout_file

    monkeypatch.setattr(layout_file, "BUNDLED_DIR", tmp_path / "b")
    (tmp_path / "b").mkdir()
    user = tmp_path / "u"
    user.mkdir()
    (user / "s.yaml").write_text(
        "name: s\ndefault: status\nschedule:\n  - {layout: status}\ncycle: [nope]\n")
    result = layout_file.load_all(user)
    assert "s" not in result.layouts
    assert any("unknown layout 'nope'" in e for e in result.errors[str(user / "s.yaml")])
