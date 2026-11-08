"""SVG -> panel PNG pipeline."""

import io

import pytest
from PIL import Image

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.pipeline import (
    ImageTooLargeError,
    PanelProfile,
    PipelineError,
    render,
)

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="480">'
       '<rect width="800" height="480" fill="#fff"/>'
       '<rect x="10" y="10" width="200" height="100" fill="#888"/>'
       '<text x="20" y="200" font-family="TRMNL16" font-size="16">Kök 20,9°</text>'
       '<text x="20" y="320" font-family="Inter" font-weight="700" font-size="74">3,1°</text>'
       "</svg>")


def _decode(png: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(png))
    img.load()
    return img


def test_1bit_is_pure_black_and_white() -> None:
    frame = render(SVG, PanelProfile(), FONT_DIR)
    img = _decode(frame.png)
    assert img.size == (800, 480)
    assert img.mode == "1"
    assert set(img.convert("L").tobytes()) == {0, 255}
    assert len(frame.png) < 90_000
    assert len(frame.sha) == 16


def test_2bit_has_four_levels_at_most() -> None:
    frame = render(SVG, PanelProfile(bit_depth=2), FONT_DIR)
    img = _decode(frame.png)
    assert img.size == (800, 480)
    levels = set(img.convert("L").tobytes())
    assert levels <= {0, 85, 170, 255}
    assert 85 in levels or 170 in levels  # the #888 block survives as a grey


def test_same_svg_same_hash() -> None:
    assert render(SVG, PanelProfile(), FONT_DIR).sha == render(SVG, PanelProfile(), FONT_DIR).sha


def test_byte_limit_enforced() -> None:
    with pytest.raises(ImageTooLargeError):
        render(SVG, PanelProfile(byte_limit=100), FONT_DIR)


def test_wrong_size_rejected() -> None:
    with pytest.raises(PipelineError):
        render(SVG.replace('width="800"', 'width="700"', 1), PanelProfile(), FONT_DIR)


def test_garbage_rejected() -> None:
    with pytest.raises(PipelineError):
        render("<svg nonsense", PanelProfile(), FONT_DIR)
