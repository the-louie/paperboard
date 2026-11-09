"""Render the README images: python scripts/readme_images.py [--lang sv]

The owner fixture (tests/test_layout_tidslinjen.py) with English room, calendar and screen
names, in the default language (British English) unless --lang says otherwise. Translators use
--lang to look at their language; only the default-language images belong in docs/images/.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import custom_components.paperboard.widget_registry  # noqa: E402, F401
from custom_components.paperboard import i18n  # noqa: E402
from custom_components.paperboard.compose import render_spec  # noqa: E402
from custom_components.paperboard.fonts import FONT_DIR, load_fonts  # noqa: E402
from custom_components.paperboard.layout_file import load_all  # noqa: E402
from custom_components.paperboard.pipeline import PanelProfile, render  # noqa: E402
from custom_components.paperboard.style import Theme  # noqa: E402
from custom_components.paperboard.text import Measurer  # noqa: E402
from tests.test_empty_house import EMPTY  # noqa: E402
from tests.test_layout_tidslinjen import english_owner_snapshot  # noqa: E402

LAYOUTS = ["tidslinjen", "tidningen", "bento", "tavlan", "trmnl", "almanackan", "energi"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", default=i18n.DEFAULT_LANG)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "images")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    specs = load_all(None).layouts
    measure = Measurer(load_fonts())
    snap = english_owner_snapshot(lang=args.lang)
    jobs = [(name, specs[name], snap) for name in LAYOUTS]
    jobs.append(("empty_house", specs["tidslinjen"],
                 dataclasses.replace(EMPTY, lang=args.lang, screen_name="Empty")))
    for name, spec, s in jobs:
        notes: list[str] = []
        frame = render(render_spec(spec, s, measure, Theme(), notes), PanelProfile(), FONT_DIR)
        (args.out / f"{name}.png").write_bytes(frame.png)
        print(f"{name}.png  {len(frame.png):,} B" + (f"  notes: {notes}" if notes else ""))


if __name__ == "__main__":
    main()
