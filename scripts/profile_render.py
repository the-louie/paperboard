# ruff: noqa: B023 - each lambda runs immediately inside timed()
"""B-088: where does one render's time go? Phases per bundled YAML layout, 10 runs, median.

python -m scripts.profile_render      (owner fixture; no Home Assistant needed)
"""

import datetime as dt
import io
import json
import statistics
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import resvg_py
from PIL import Image

from custom_components.paperboard import pipeline
from custom_components.paperboard.compose import as_layout
from custom_components.paperboard.fonts import load_fonts
from custom_components.paperboard.layout_file import load_all
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer

FIXTURE = Path(__file__).parent.parent / "tests/fixtures/states/owner_2026-11-08.json"
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))
PROFILE = pipeline.PanelProfile(800, 480, 1, 90_000)
# The owner's role bindings on ha-host (2026-11-08), so widgets draw real content.
ROLES = {"weather": "weather.forecast_home", "outdoor_temp": "sensor.ecowitt_temp",
         "indoor_temp": "sensor.hallen_temperatur", "feels_like": "sensor.ecowitt_feelslike",
         "outdoor_humidity": "sensor.ecowitt_humidity", "rain_today": "sensor.ecowitt_dailyrain",
         "price": "sensor.nordpool_kwh_se3_sek_2_10_025",
         "solar_forecast_today": "sensor.energy_production_today",
         "solar_power": "sensor.pv_1_power", "grid_power": "sensor.power_meter_active_power",
         "house_power": "sensor.house_usage_w", "house_energy_today": "sensor.house_load_today",
         "battery_soc": "sensor.battery_state_of_capacity", "sun": "sun.sun",
         "rooms": ["sensor.v1_koket_temp_temp", "sensor.tvrum_temp_temperatur",
                   "sensor.hallen_temperatur", "sensor.v1_badrum_temphumid_temp",
                   "sensor.v0_kallare_th_temp", "sensor.ecowitt_tempin"],
         "grid_export_positive": True}


def timed(fn):
    t = time.perf_counter()
    out = fn()
    return out, (time.perf_counter() - t) * 1000


def main() -> None:
    t0 = time.perf_counter()
    fonts = load_fonts()
    measure = Measurer(fonts)
    print(f"cold: load_fonts+Measurer {(time.perf_counter() - t0) * 1000:.0f} ms")
    states = json.loads(FIXTURE.read_text())["states"]
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="Hallen", states=states,
                    battery=100, roles=ROLES)
    specs = load_all(None).layouts
    for name in sorted(specs):
        layout = as_layout(specs[name], lambda: Theme(bit_depth=1))
        rows = {"build": [], "resvg": [], "decode": [], "quantize": [], "png": []}
        for _ in range(10):
            svg, ms = timed(lambda: layout.build(snap, measure))
            rows["build"].append(ms)
            data, ms = timed(lambda: bytes(resvg_py.svg_to_bytes(
                svg_string=pipeline._ensure_crisp(svg), font_dirs=[str(fonts.font_dir)],
                skip_system_fonts=True)))
            rows["resvg"].append(ms)
            gray, ms = timed(lambda: Image.open(io.BytesIO(data)).convert("L"))
            rows["decode"].append(ms)
            q, ms = timed(lambda: pipeline.QUANTIZERS[1](gray))
            rows["quantize"].append(ms)
            _, ms = timed(lambda: pipeline.encode_png_gray(q, 800, 480, 1))
            rows["png"].append(ms)
        med = {k: statistics.median(v) for k, v in rows.items()}
        print(f"{name:11s} total {sum(med.values()):6.0f} ms  " +
              "  ".join(f"{k} {v:5.0f}" for k, v in med.items()))


if __name__ == "__main__":
    main()
