"""Minimal SVG builder. Everything black or white; greys only via patterns (1-bit safe)."""

from __future__ import annotations

from xml.sax.saxutils import escape

from .text import TextStyle

BLACK, WHITE = "#000", "#fff"

PATTERNS = {
    # 1 black pixel in every 3x3 cell: a light "night" tint that survives thresholding.
    "dots": '<pattern id="dots" width="3" height="3" patternUnits="userSpaceOnUse">'
            '<rect width="1" height="1" fill="#000"/></pattern>',
    # 50 % checkerboard: "past" or "inactive" fill.
    "checker": '<pattern id="checker" width="2" height="2" patternUnits="userSpaceOnUse">'
               '<rect width="1" height="1" fill="#000"/><rect x="1" y="1" width="1" '
               'height="1" fill="#000"/></pattern>',
    # Diagonal hatch: forecast/estimate areas.
    "hatch": '<pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse">'
             '<path d="M-1,1 L1,-1 M0,4 L4,0 M3,5 L5,3" stroke="#000" stroke-width="1"/>'
             "</pattern>",
}


def _num(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Svg:
    """Collects elements; str() gives the document with only the patterns actually used."""

    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self._parts: list[str] = []
        self._used: set[str] = set()

    def raw(self, fragment: str) -> None:
        self._parts.append(fragment)

    def fill(self, paint: str) -> str:
        if paint in PATTERNS:
            self._used.add(paint)
            return f"url(#{paint})"
        return paint

    def rect(self, x: float, y: float, w: float, h: float, fill: str = BLACK,
             stroke: str | None = None, stroke_width: float = 2, rx: float = 0) -> None:
        if w <= 0 or h <= 0:
            return
        extra = f' stroke="{stroke}" stroke-width="{_num(stroke_width)}"' if stroke else ""
        radius = f' rx="{_num(rx)}"' if rx else ""
        self._parts.append(f'<rect x="{_num(x)}" y="{_num(y)}" width="{_num(w)}" '
                           f'height="{_num(h)}" fill="{self.fill(fill)}"{extra}{radius}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float = 2,
             dash: str | None = None, color: str = BLACK) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._parts.append(f'<line x1="{_num(x1)}" y1="{_num(y1)}" x2="{_num(x2)}" '
                           f'y2="{_num(y2)}" stroke="{color}" stroke-width="{_num(width)}"{d}/>')

    def path(self, d: str, fill: str = "none", stroke: str | None = BLACK,
             width: float = 2) -> None:
        s = f' stroke="{stroke}" stroke-width="{_num(width)}" stroke-linejoin="round"' \
            if stroke else ""
        self._parts.append(f'<path d="{d}" fill="{self.fill(fill)}"{s}/>')

    def text(self, x: float, y: float, content: str, style: TextStyle, anchor: str = "start",
             color: str = BLACK) -> None:
        if not content:
            return
        self._parts.append(
            f'<text x="{_num(x)}" y="{_num(y)}" font-family="{style.family}" '
            f'font-weight="{style.weight}" font-size="{style.size}" text-anchor="{anchor}" '
            f'fill="{color}">{escape(content)}</text>')

    def __str__(self) -> str:
        defs = "".join(PATTERNS[p] for p in sorted(self._used))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
                f'height="{self.height}" shape-rendering="crispEdges" '
                f'text-rendering="optimizeSpeed">'
                f"{f'<defs>{defs}</defs>' if defs else ''}"
                f'<rect width="{self.width}" height="{self.height}" fill="#fff"/>'
                + "".join(self._parts) + "</svg>")
