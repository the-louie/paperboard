"""Grid tracks, areas, rules and reflow."""

import pytest

from custom_components.paperboard.grid import Grid, GridError, solve_tracks

AREAS = ["header header", "now timeline", "days energy", "footer footer"]


def _grid() -> Grid:
    return Grid.build([250, "fr"], [40, 262, "fr", 26], AREAS, 800, 480)


def test_tracks() -> None:
    assert solve_tracks([250, "fr"], 800) == [250, 550]
    assert solve_tracks(["fr", "2fr", 100], 400) == [100, 200, 100]
    with pytest.raises(GridError):
        solve_tracks([500, 400, "fr"], 800)
    with pytest.raises(GridError):
        solve_tracks(["auto"], 800)


def test_rects() -> None:
    g = _grid()
    assert (r := g.rect("header")).x == 0 and r.w == 800 and r.h == 40
    assert (r := g.rect("timeline")).x == 250 and r.y == 40 and r.w == 550 and r.h == 262
    assert g.rect("days").h == 480 - 40 - 262 - 26


def test_validation() -> None:
    with pytest.raises(GridError, match="not a rectangle"):
        Grid.build([1, 1], [1, 1], ["a b", "b b"], 2, 2)
    with pytest.raises(GridError, match="names for"):
        Grid.build([1, 1], [1], ["a"], 2, 1)


def test_collapse_merges_and_drops_rule() -> None:
    g = _grid()
    assert (250, 40, 250, 454) in g.rules()  # now|timeline and days|energy, one line
    assert g.collapse("now", None) == "timeline"
    assert g.rect("timeline").x == 0 and g.rect("timeline").w == 800
    assert (250, 302, 250, 454) in g.rules()  # only days|energy keeps its divider
    assert (250, 40, 250, 454) not in g.rules()


def test_collapse_refuses_partial_edge() -> None:
    g = Grid.build(["fr", "fr"], ["fr", "fr"], ["a b", "a c"], 2, 2)
    assert g.neighbour("a", "right") is None  # b and c both touch a's edge
    assert g.collapse("a", None) is None
    assert g.collapse("b", "down") == "c"


def test_rules_are_merged_lines() -> None:
    g = _grid()
    rules = g.rules()
    assert (0, 40, 800, 40) in rules  # header bottom, one full-width line
    assert (0, 454, 800, 454) in rules
