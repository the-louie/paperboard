"""Type scale and bit-depth-aware style tokens (docs/design/layout-schema.md).

Small text uses the TRMNL pixel fonts at their native sizes only; large numerals use Inter.
Greys exist only on >=2-bit panels; on 1-bit they become patterns that survive thresholding.
"""

from __future__ import annotations

from dataclasses import dataclass

from .svg import BLACK, WHITE
from .text import TextStyle

PIXEL_SIZES = (12, 16, 21)
SCALE: dict[str, tuple[str, int]] = {
    "xs": ("TRMNL12", 12), "s": ("TRMNL16", 16), "m": ("TRMNL21", 21),
    "l": ("Inter", 26), "xl": ("Inter", 38), "xxl": ("Inter", 58), "hero": ("Inter", 74),
}
INTER_WEIGHTS = {"regular": 500, "bold": 700, "heavy": 800}


@dataclass(frozen=True)
class Theme:
    """Everything a widget needs to pick fonts and fills for one panel."""

    bit_depth: int = 1
    scale_factor: float = 1.0

    def text(self, size: str, bold: bool = False) -> TextStyle:
        family, px = SCALE[size]
        if family.startswith("TRMNL"):
            target = px * self.scale_factor
            native = min(PIXEL_SIZES, key=lambda n: abs(n - target))
            return TextStyle(f"TRMNL{native}", 700 if bold else 400, native)
        return TextStyle(family, INTER_WEIGHTS["bold" if bold else "regular"],
                         round(px * self.scale_factor))

    def numeral(self, size: str = "hero") -> TextStyle:
        """Large figures are always Inter Bold, even at sizes the scale maps to pixel fonts."""
        px = SCALE[size][1]
        return TextStyle("Inter", INTER_WEIGHTS["bold"], round(px * self.scale_factor))

    # --- fills -------------------------------------------------------------------------
    @property
    def ink(self) -> str:
        return BLACK

    @property
    def paper(self) -> str:
        return WHITE

    @property
    def tint(self) -> str:
        """Light background marking (night, 'not now')."""
        return ("#cccccc" if self.bit_depth >= 4 else "#aaaaaa") if self.bit_depth >= 2 \
            else "dots"

    @property
    def past(self) -> str:
        """Mid fill for elapsed or inactive bars."""
        return "#555555" if self.bit_depth >= 2 else "checker"

    @property
    def estimate(self) -> str:
        """Forecast / estimated quantities (expected solar)."""
        return "#aaaaaa" if self.bit_depth >= 2 else "hatch"

    def px(self, value: float) -> float:
        return value * self.scale_factor
