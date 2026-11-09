"""Render the README images in English: python scripts/readme_images.py

Same data as the owner golden tests (tests/test_layout_tidslinjen.py), but with lang="en" and
English room, calendar and screen names, so the README speaks to an international audience.
The golden images stay Swedish; they test the default language.
"""

from __future__ import annotations

import copy
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import custom_components.paperboard.widget_registry  # noqa: E402, F401
from custom_components.paperboard.compose import render_spec  # noqa: E402
from custom_components.paperboard.fonts import FONT_DIR, load_fonts  # noqa: E402
from custom_components.paperboard.layout_file import load_all  # noqa: E402
from custom_components.paperboard.pipeline import PanelProfile, render  # noqa: E402
from custom_components.paperboard.style import Theme  # noqa: E402
from custom_components.paperboard.text import Measurer  # noqa: E402
from tests.test_empty_house import EMPTY  # noqa: E402
from tests.test_layout_tidslinjen import owner_snapshot  # noqa: E402

OUT = ROOT / "docs" / "images"
ROOM_NAMES = {
    "sensor.v1_koket_temp_temp": "Kitchen",
    "sensor.tvrum_temp_temperatur": "TV room",
    "sensor.hallen_temperatur": "Hall",
    "sensor.v1_badrum_temphumid_temp": "Bathroom",
    "sensor.v1_sovrum_a_temperatur": "Bedroom A",
    "sensor.v2_sovrum_b_temperatur": "Bedroom B",
    "sensor.ecowitt_tempin": "Sunroom",
}
SUMMARIES = {"Jobb": "Work"}
LAYOUTS = ["tidslinjen", "tidningen", "bento", "tavlan", "trmnl", "almanackan", "energi"]


def english_snapshot():
    snap = owner_snapshot(lang="en")
    states = copy.deepcopy(snap.states)
    for entity, name in ROOM_NAMES.items():
        states[entity]["attributes"]["friendly_name"] = name
    events = {cal: [{**e, "summary": SUMMARIES.get(e.get("summary"), e.get("summary"))}
                    for e in evs] for cal, evs in snap.events.items()}
    return dataclasses.replace(snap, states=states, events=events, screen_name="Hall")


def main() -> None:
    specs = load_all(None).layouts
    measure = Measurer(load_fonts())
    snap = english_snapshot()
    jobs = [(name, specs[name], snap) for name in LAYOUTS]
    jobs.append(("empty_house", specs["tidslinjen"],
                 dataclasses.replace(EMPTY, lang="en", screen_name="Empty")))
    for name, spec, s in jobs:
        notes: list[str] = []
        frame = render(render_spec(spec, s, measure, Theme(), notes), PanelProfile(), FONT_DIR)
        (OUT / f"{name}.png").write_bytes(frame.png)
        print(f"{name}.png  {len(frame.png):,} B" + (f"  notes: {notes}" if notes else ""))


if __name__ == "__main__":
    main()
