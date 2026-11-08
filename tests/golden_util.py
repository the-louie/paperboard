"""Golden-image comparison: exact pixel match, readable failure.

Set PAPERBOARD_UPDATE_GOLDEN=1 (or run scripts/update_golden.py) to (re)write goldens.
On mismatch the actual image and a diff (changed pixels black on white) are written to
tests/output/ and the assertion names them.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

from PIL import Image, ImageChops

GOLDEN_DIR = Path(__file__).parent / "golden"
OUTPUT_DIR = Path(__file__).parent / "output"


def _load(png: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(png))
    img.load()
    return img.convert("L")


def compare(actual_png: bytes, golden_png: bytes) -> tuple[int, Image.Image | None]:
    """Number of differing pixels and a diff image (None when identical)."""
    a, g = _load(actual_png), _load(golden_png)
    if a.size != g.size:
        return a.width * a.height, None
    diff = ImageChops.difference(a, g).point(lambda v: 255 if v else 0)
    changed = diff.histogram()[255]
    return changed, (ImageChops.invert(diff) if changed else None)


def assert_golden(name: str, actual_png: bytes) -> None:
    path = GOLDEN_DIR / f"{name}.png"
    if os.environ.get("PAPERBOARD_UPDATE_GOLDEN") == "1" or not path.exists():
        if not path.exists() and os.environ.get("CI"):
            raise AssertionError(f"golden {path} missing (never created in CI)")
        path.write_bytes(actual_png)
        return
    changed, diff = compare(actual_png, path.read_bytes())
    if changed:
        OUTPUT_DIR.mkdir(exist_ok=True)
        (OUTPUT_DIR / f"{name}.actual.png").write_bytes(actual_png)
        if diff is not None:
            diff.save(OUTPUT_DIR / f"{name}.diff.png")
        raise AssertionError(
            f"{name}: {changed} pixels differ from {path}; see {OUTPUT_DIR}/{name}.*.png"
        )
