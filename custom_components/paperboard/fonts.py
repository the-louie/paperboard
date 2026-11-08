"""Bundled font registry.

resvg loads the fonts itself from FONT_DIR; Pillow fonts are loaded here for text
measurement. Loading opens files, so call load_fonts() in an executor job.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import ImageFont

FONT_DIR = Path(__file__).parent / "fonts"

# family name as used in SVG font-family, weight -> file
FONT_FILES: dict[tuple[str, int], str] = {
    ("TRMNL12", 400): "TRMNL12-Regular.ttf",
    ("TRMNL12", 700): "TRMNL12-Bold.ttf",
    ("TRMNL16", 400): "TRMNL16-Regular.ttf",
    ("TRMNL16", 700): "TRMNL16-Bold.ttf",
    ("TRMNL21", 400): "TRMNL21-Regular.ttf",
    ("TRMNL21", 700): "TRMNL21-Bold.ttf",
    ("Inter", 500): "Inter-Medium.ttf",
    ("Inter", 700): "Inter-Bold.ttf",
    ("Inter", 800): "Inter-ExtraBold.ttf",
}

# Pixel fonts are only crisp at their design size.
PIXEL_FONT_SIZE = {"TRMNL12": 12, "TRMNL16": 16, "TRMNL21": 21}


@dataclass(frozen=True)
class FontRegistry:
    """Paths for resvg plus file bytes for building Pillow fonts at any size."""

    font_dir: Path
    data: dict[tuple[str, int], bytes]

    def pillow(self, family: str, weight: int, size: int) -> ImageFont.FreeTypeFont:
        """A Pillow font; cheap enough to call per measurement (no file I/O)."""
        return ImageFont.truetype(BytesIO(self.data[(family, weight)]), size)


def load_fonts(font_dir: Path = FONT_DIR) -> FontRegistry:
    """Read every bundled font (blocking I/O)."""
    data = {key: (font_dir / name).read_bytes() for key, name in FONT_FILES.items()}
    return FontRegistry(font_dir=font_dir, data=data)
