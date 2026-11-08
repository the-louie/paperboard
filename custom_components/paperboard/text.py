"""Text measurement, truncation and wrapping in advance widths (see docs/design/rendering.md).

Pillow's getlength() matches resvg's advance exactly for the TRMNL fonts and within 0.8 px
for Inter, so SAFETY px are kept free when fitting.
"""

from __future__ import annotations

from dataclasses import dataclass

from .fonts import FontRegistry

ELLIPSIS = "…"
SAFETY = 1.0


@dataclass(frozen=True)
class TextStyle:
    """Font family, weight and pixel size as used in the SVG."""

    family: str
    weight: int
    size: int


class Measurer:
    """Measures strings for one FontRegistry, caching Pillow fonts per style."""

    def __init__(self, fonts: FontRegistry) -> None:
        self._fonts = fonts
        self._cache: dict[TextStyle, object] = {}

    def width(self, text: str, style: TextStyle) -> float:
        font = self._cache.get(style)
        if font is None:
            font = self._fonts.pillow(style.family, style.weight, style.size)
            self._cache[style] = font
        return font.getlength(text)  # type: ignore[attr-defined]

    def fits(self, text: str, style: TextStyle, max_width: float) -> bool:
        return self.width(text, style) <= max_width - SAFETY

    def truncate(self, text: str, style: TextStyle, max_width: float) -> str:
        """Longest prefix that fits, with an ellipsis if anything was cut."""
        if self.fits(text, style, max_width):
            return text
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.fits(text[:mid].rstrip() + ELLIPSIS, style, max_width):
                lo = mid
            else:
                hi = mid - 1
        return text[:lo].rstrip() + ELLIPSIS if lo else ""

    def wrap(self, text: str, style: TextStyle, max_width: float, max_lines: int) -> list[str]:
        """Greedy word wrap; the last allowed line is truncated with an ellipsis."""
        lines: list[str] = []
        words = text.split()
        current = ""
        for i, word in enumerate(words):
            candidate = f"{current} {word}".strip()
            if self.fits(candidate, style, max_width):
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                rest = " ".join([word, *words[i + 1 :]])
                lines.append(self.truncate(rest, style, max_width))
                return lines
        if current:
            lines.append(self.truncate(current, style, max_width))
        return lines[:max_lines]
