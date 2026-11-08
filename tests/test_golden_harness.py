"""The golden harness itself: identical passes, a 1-px change fails readably."""

import io

import pytest
from PIL import Image

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.pipeline import PanelProfile, render
from tests.golden_util import OUTPUT_DIR, assert_golden, compare

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="480">'
       '<rect width="800" height="480" fill="#fff"/>'
       '<text x="20" y="40" font-family="TRMNL21" font-size="21">Golden harness</text>'
       '<line x1="0" y1="50" x2="800" y2="50" stroke="#000" stroke-width="2"/></svg>')


def _flip_pixel(png: bytes) -> bytes:
    img = Image.open(io.BytesIO(png)).convert("L")
    img.putpixel((400, 300), 0 if img.getpixel((400, 300)) else 255)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def test_harness_sample_golden() -> None:
    assert_golden("harness_sample", render(SVG, PanelProfile(), FONT_DIR).png)


def test_one_pixel_change_is_caught() -> None:
    png = render(SVG, PanelProfile(), FONT_DIR).png
    changed, diff = compare(_flip_pixel(png), png)
    assert changed == 1
    assert diff is not None and diff.getpixel((400, 300)) == 0


def test_failure_message_names_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PAPERBOARD_UPDATE_GOLDEN", raising=False)
    png = render(SVG, PanelProfile(), FONT_DIR).png
    with pytest.raises(AssertionError, match="1 pixels differ"):
        assert_golden("harness_sample", _flip_pixel(png))
    assert (OUTPUT_DIR / "harness_sample.diff.png").exists()
