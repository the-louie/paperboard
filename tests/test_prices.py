"""Price adapters: owner's HACS nordpool shape, bare floats, ENTSO-e, core service, garbage."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.paperboard.prices import PriceSnapshot, from_service, from_state

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)
FIXTURE = Path(__file__).parent / "fixtures/states/owner_2026-11-08.json"


def _owner_state() -> dict:
    return json.loads(FIXTURE.read_text())["states"]["sensor.nordpool_kwh_se3_sek_2_10_025"]


def test_owner_nordpool_raw_today() -> None:
    series = from_state(_owner_state(), NOW)
    assert len(series.points) == 96
    assert series.points[0].start == dt.datetime(2026, 11, 8, 0, 0, tzinfo=TZ)
    assert series.unit == "SEK/kWh" and series.includes_fees is True
    hourly = series.hourly()
    assert len(hourly) == 24 and hourly[0].end - hourly[0].start == dt.timedelta(hours=1)
    start, mean = series.cheapest_window(2, NOW)
    assert start >= NOW.replace(minute=0) and 0 < mean < 5


def test_bare_floats_and_cents() -> None:
    state = {"state": "150", "attributes": {"today": [100.0] * 24, "tomorrow": [],
                                            "price_in_cents": True}}
    series = from_state(state, NOW)
    assert len(series.points) == 24 and series.points[0].value == 1.0
    assert series.current == 1.5


def test_entsoe_shape() -> None:
    state = {"state": "0.3", "attributes": {"prices_today": [
        {"time": "2026-11-08T00:00:00+01:00", "price": 0.2},
        {"time": "2026-11-08T01:00:00+01:00", "price": 0.3}]}}
    series = from_state(state, NOW)
    assert [p.value for p in series.points] == [0.2, 0.3]
    assert series.points[1].end - series.points[1].start == dt.timedelta(hours=1)


def test_core_service_mwh_to_kwh() -> None:
    resp = {"SE3": [{"start": "2026-11-08T00:00:00+01:00", "end": "2026-11-08T01:00:00+01:00",
                     "price": 1234.0}]}
    series = from_service(resp, "SE3", "SEK")
    assert series.points[0].value == 1.234 and series.includes_fees is False


def test_garbage_never_raises() -> None:
    for state in (None, {}, {"state": "unavailable", "attributes": {"raw_today": "x"}},
                  {"state": "1", "attributes": {"today": [1, None, "a"]}},
                  {"state": "1", "attributes": {"raw_today": [{"start": "bad", "value": 1}]}}):
        series = from_state(state, NOW)
        assert series.cheapest_window(2, NOW) is None or series.points


def test_snapshot_roundtrip() -> None:
    series = from_state(_owner_state(), NOW)
    assert PriceSnapshot.of(series).series() == series


async def test_core_nordpool_provider(hass) -> None:
    from homeassistant.core import SupportsResponse
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant.common import MockConfigEntry

    from custom_components.paperboard.data import PriceProvider

    np_entry = MockConfigEntry(domain="nordpool", data={"currency": "SEK", "areas": ["SE3"]})
    np_entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create("sensor", "nordpool", "se3_price",
                                           config_entry=np_entry,
                                           suggested_object_id="se3_price")
    calls = []

    async def handler(call):
        calls.append(call.data["date"])
        day = call.data["date"]
        return {"SE3": [{"start": f"{day}T00:00:00+01:00", "end": f"{day}T01:00:00+01:00",
                         "price": 2000.0}]}

    hass.services.async_register("nordpool", "get_prices_for_date", handler,
                                 supports_response=SupportsResponse.ONLY)
    provider = PriceProvider(hass, "sensor.se3_price")
    await provider.async_refresh()
    series = provider.series()
    assert len(calls) == 2 and len(series.points) == 2
    assert series.points[0].value == 2.0 and series.unit == "SEK/kWh"
