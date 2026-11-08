"""CSS-grid-like layout engine: tracks, named areas, rules, and reflow when a widget is empty.

Reflow works on the cell map: collapsing area A into neighbour B relabels A's cells as B. The
union is rectangular because B must share A's full edge. Rules are drawn only where adjacent
cells belong to different areas, so a collapsed boundary loses its rule automatically.
"""

from __future__ import annotations

from dataclasses import dataclass

from .widgets import Rect

EMPTY = "."
DIRECTIONS = {"left": (0, -1), "right": (0, 1), "up": (-1, 0), "down": (1, 0)}


class GridError(ValueError):
    """The grid spec is inconsistent (reported as a layout error, never raised at render)."""


def solve_tracks(tracks: list[int | str], total: float, gap: float = 0) -> list[float]:
    """Pixel sizes for tracks of fixed px and 'fr' / 'Nfr' shares of the remainder."""
    fixed, shares = 0.0, []
    for t in tracks:
        if isinstance(t, int | float):
            fixed += t
            shares.append(0.0)
        else:
            text = str(t).strip()
            if not text.endswith("fr"):
                raise GridError(f"track {t!r}: use a number of px or 'fr'")
            shares.append(float(text[:-2] or 1))
    free = total - fixed - gap * (len(tracks) - 1)
    if free < 0 and sum(shares):
        raise GridError(f"fixed tracks ({fixed:.0f} px) exceed the canvas ({total:.0f} px)")
    per = free / sum(shares) if sum(shares) else 0
    return [per * s if s else float(t) for t, s in zip(tracks, shares, strict=True)]


@dataclass
class Grid:
    columns: list[float]
    rows: list[float]
    cells: list[list[str]]
    gap: float = 0.0

    @classmethod
    def build(cls, columns: list[int | str], rows: list[int | str], areas: list[str],
              width: float, height: float, gap: float = 0.0) -> Grid:
        cells = [row.split() for row in areas]
        if len(cells) != len(rows):
            raise GridError(f"{len(cells)} area rows for {len(rows)} grid rows")
        for i, row in enumerate(cells):
            if len(row) != len(columns):
                raise GridError(f"area row {i} has {len(row)} names for {len(columns)} columns")
        grid = cls(solve_tracks(columns, width, gap), solve_tracks(rows, height, gap), cells, gap)
        for name in grid.names():
            grid._check_rectangular(name)
        return grid

    def names(self) -> list[str]:
        seen: dict[str, None] = {}
        for row in self.cells:
            for name in row:
                if name != EMPTY:
                    seen.setdefault(name)
        return list(seen)

    def _span(self, name: str) -> tuple[int, int, int, int]:
        coords = [(r, c) for r, row in enumerate(self.cells) for c, n in enumerate(row)
                  if n == name]
        if not coords:
            raise GridError(f"unknown area {name!r}")
        rs, cs = [r for r, _ in coords], [c for _, c in coords]
        return min(rs), min(cs), max(rs), max(cs)

    def _check_rectangular(self, name: str) -> None:
        r0, c0, r1, c1 = self._span(name)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if self.cells[r][c] != name:
                    raise GridError(f"area {name!r} is not a rectangle")

    def rect(self, name: str) -> Rect:
        r0, c0, r1, c1 = self._span(name)
        g = self.gap
        x, y = sum(self.columns[:c0]) + g * c0, sum(self.rows[:r0]) + g * r0
        return Rect(x, y, sum(self.columns[c0:c1 + 1]) + g * (c1 - c0),
                    sum(self.rows[r0:r1 + 1]) + g * (r1 - r0))

    def neighbour(self, name: str, direction: str) -> str | None:
        """The single area sharing `name`'s whole edge in `direction`, if any."""
        r0, c0, r1, c1 = self._span(name)
        dr, dc = DIRECTIONS[direction]
        if dr:
            r = r0 - 1 if dr < 0 else r1 + 1
            if not 0 <= r < len(self.rows):
                return None
            edge = {self.cells[r][c] for c in range(c0, c1 + 1)}
        else:
            c = c0 - 1 if dc < 0 else c1 + 1
            if not 0 <= c < len(self.columns):
                return None
            edge = {self.cells[r][c] for r in range(r0, r1 + 1)}
        if len(edge) != 1 or EMPTY in edge:
            return None
        other = edge.pop()
        # The neighbour must not stick out past name's edge either (union stays rectangular).
        o0, oc0, o1, oc1 = self._span(other)
        if (dr and (oc0, oc1) != (c0, c1)) or (dc and (o0, o1) != (r0, r1)):
            return None
        return other

    def collapse(self, name: str, direction: str | None) -> str | None:
        """Give `name`'s cells to its neighbour; returns who took them (None = left blank)."""
        dirs = [direction] if direction else ["right", "left"]
        for d in dirs:
            if d == "none":
                return None
            if (other := self.neighbour(name, d)) is not None:
                self.cells = [[other if n == name else n for n in row] for row in self.cells]
                return other
        return None

    def rules(self) -> list[tuple[float, float, float, float]]:
        """Line segments where adjacent cells belong to different (non-empty) areas."""
        segs = []
        g = self.gap
        # A rule sits in the middle of the gap between two tracks.
        xs = [sum(self.columns[:i]) + g * i - (g / 2 if 0 < i < len(self.columns) else 0)
              for i in range(len(self.columns) + 1)]
        ys = [sum(self.rows[:i]) + g * i - (g / 2 if 0 < i < len(self.rows) else 0)
              for i in range(len(self.rows) + 1)]
        for r, row in enumerate(self.cells):
            for c, name in enumerate(row):
                if c + 1 < len(row) and name != row[c + 1]:
                    segs.append((xs[c + 1], ys[r], xs[c + 1], ys[r + 1]))
                if r + 1 < len(self.cells) and name != self.cells[r + 1][c]:
                    segs.append((xs[c], ys[r + 1], xs[c + 1], ys[r + 1]))
        return _merge_segments(segs)


def _merge_segments(segs: list[tuple[float, float, float, float]]
                    ) -> list[tuple[float, float, float, float]]:
    """Join collinear touching segments so each rule is one line."""
    horiz: dict[float, list[list[float]]] = {}
    vert: dict[float, list[list[float]]] = {}
    for x1, y1, x2, y2 in segs:
        if y1 == y2:
            horiz.setdefault(y1, []).append([x1, x2])
        else:
            vert.setdefault(x1, []).append([y1, y2])
    out: list[tuple[float, float, float, float]] = []
    for key, spans, horizontal in [*((k, v, True) for k, v in horiz.items()),
                                   *((k, v, False) for k, v in vert.items())]:
        merged: list[list[float]] = []
        for a, b in sorted(spans):
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        for a, b in merged:
            out.append((a, key, b, key) if horizontal else (key, a, key, b))
    return sorted(out)
