"""Snapshot a home's states and service responses into a test fixture (read-only).

Usage:
    python scripts/capture_fixture.py <settings.local.json> <out.json> [--name NAME]

<settings.local.json> holds {"env": {"HASS_URL": ..., "HASS_TOKEN": ...}}. The token is only
read, never written or printed. Only the entities in ENTITIES are captured, so persons, zones
and device trackers (locations) never enter a fixture. Calendar entity ids (which can contain
names) and event summaries are replaced with placeholders; descriptions and
locations are dropped.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.parse
import urllib.request
from typing import Any

# The owner's entities for the mockups, by role. Missing ones are simply skipped.
ENTITIES = [
    "weather.forecast_home",
    "sensor.ecowitt_temp", "sensor.ecowitt_tempin", "sensor.ecowitt_humidity",
    "sensor.ecowitt_feelslike", "sensor.ecowitt_windspeed", "sensor.ecowitt_windgust",
    "sensor.ecowitt_winddir_name", "sensor.ecowitt_baromrel", "sensor.ecowitt_dailyrain",
    "sensor.ecowitt_dewpoint",
    "sensor.nordpool_kwh_se3_sek_2_10_025",
    "sensor.energy_production_today", "sensor.energy_production_today_remaining",
    "sensor.energy_production_tomorrow", "sensor.power_production_now",
    "sensor.pv_1_power", "sensor.inverter_daily_yield", "sensor.house_usage_w",
    "sensor.house_load_today", "sensor.power_meter_active_power",
    "sensor.battery_state_of_capacity",
    "sensor.v1_koket_temp_temp", "sensor.tvrum_temp_temperatur", "sensor.hallen_temperatur",
    "sensor.v1_badrum_temphumid_temp", "sensor.v1_sovrum_a_temperatur",
    "sensor.v2_sovrum_b_temperatur", "sensor.v0_kallare_th_temp",
    "sensor.v2_vind_temp_temperatur",
    "sun.sun",
    "binary_sensor.trmnl_schoolday",
]
CALENDARS = ["calendar.family", "calendar.jobb", "calendar.holidays_in_sweden"]
KEEP_ATTRS_DROP = {"entity_picture", "latitude", "longitude", "gps_accuracy"}


def _req(base: str, token: str, path: str, data: dict | None = None) -> Any:
    req = urllib.request.Request(
        base + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def capture(base: str, token: str) -> dict[str, Any]:
    states: dict[str, Any] = {}
    for entity_id in ENTITIES:
        try:
            st = _req(base, token, f"/api/states/{entity_id}")
        except Exception:
            continue
        attrs = {k: v for k, v in st["attributes"].items() if k not in KEEP_ATTRS_DROP}
        states[entity_id] = {"state": st["state"], "attributes": attrs,
                             "last_changed": st["last_changed"]}
    forecasts = {}
    for kind in ("hourly", "daily"):
        resp = _req(base, token, "/api/services/weather/get_forecasts?return_response",
                    {"entity_id": "weather.forecast_home", "type": kind})
        forecasts[kind] = resp["service_response"]["weather.forecast_home"]["forecast"]
    now = dt.datetime.now(dt.UTC)
    start, end = now.isoformat(), (now + dt.timedelta(days=7)).isoformat()
    events: dict[str, list[dict[str, Any]]] = {}
    for cal in CALENDARS:
        try:
            query = urllib.parse.urlencode({"start": start, "end": end})
            raw = _req(base, token, f"/api/calendars/{cal}?{query}")
        except Exception:
            continue
        holidays = cal == "calendar.holidays_in_sweden"
        key = cal if holidays else f"calendar.calendar_{len(events) + 1}"
        events[key] = [{"start": e["start"], "end": e["end"],
                        "summary": f"Händelse {i + 1}" if cal != "calendar.holidays_in_sweden"
                        else e.get("summary", "")}
                       for i, e in enumerate(raw)]
    return {"captured_at": now.isoformat(), "states": states,
            "weather_forecasts": {"weather.forecast_home": forecasts},
            "calendar_events": events}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("settings")
    ap.add_argument("out")
    args = ap.parse_args()
    with open(args.settings, encoding="utf-8") as fh:
        env = json.load(fh)["env"]
    data = capture(env["HASS_URL"].rstrip("/"), env["HASS_TOKEN"])
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"{len(data['states'])} states, "
          f"{sum(len(v) for v in data['calendar_events'].values())} events -> {args.out}")


if __name__ == "__main__":
    main()
