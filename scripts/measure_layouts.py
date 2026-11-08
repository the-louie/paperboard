"""Performance budget (T-29): render time and peak Python memory per layout.

python -m scripts.measure_layouts   (uses the owner fixture; 20 runs each, median)
"""

import datetime as dt
import json
import statistics
import time
import tracemalloc
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.paperboard.fonts import FONT_DIR, load_fonts
from custom_components.paperboard.layouts import LAYOUTS, Snapshot
from custom_components.paperboard.pipeline import PanelProfile, render
from custom_components.paperboard.text import Measurer
from scripts.spikes import proto_tidslinjen

FIXTURE = Path(__file__).parent.parent / "tests/fixtures/states/owner_2026-11-08.json"
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=ZoneInfo("Europe/Stockholm"))


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    measure = Measurer(load_fonts())
    snap = Snapshot(now=NOW, width=800, height=480, screen_name="Hallen",
                    states=fixture["states"], battery=100)
    cases = {name: (lambda layout=layout: layout.build(snap, measure))
             for name, layout in LAYOUTS.items()}
    cases["proto_tidslinjen"] = lambda: proto_tidslinjen.build(fixture, NOW)
    for depth in (1, 2):
        profile = PanelProfile(bit_depth=depth, byte_limit=750_000)
        for name, build in cases.items():
            times = []
            for _ in range(20):
                t = time.perf_counter()
                frame = render(build(), profile, FONT_DIR)
                times.append((time.perf_counter() - t) * 1000)
            tracemalloc.start()
            render(build(), profile, FONT_DIR)
            peak = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            print(f"{name:18} {depth}-bit  median {statistics.median(times):6.1f} ms  "
                  f"max {max(times):6.1f} ms  peak {peak / 1e6:5.1f} MB  {len(frame.png):6} B")


if __name__ == "__main__":
    main()
