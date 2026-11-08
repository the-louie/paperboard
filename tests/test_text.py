"""Text fitting helpers."""

import pytest

from custom_components.paperboard.fonts import load_fonts
from custom_components.paperboard.text import ELLIPSIS, Measurer, TextStyle

S16 = TextStyle("TRMNL16", 400, 16)


@pytest.fixture(scope="module")
def m() -> Measurer:
    return Measurer(load_fonts())


def test_width_positive_and_monotonic(m: Measurer) -> None:
    assert 0 < m.width("Kök", S16) < m.width("Köket", S16)


def test_truncate_keeps_fitting_text(m: Measurer) -> None:
    assert m.truncate("Kök 20,9°", S16, 500) == "Kök 20,9°"


def test_truncate_adds_ellipsis_and_fits(m: Measurer) -> None:
    out = m.truncate("Jobb hela dagen på kontoret", S16, 120)
    assert out.endswith(ELLIPSIS)
    assert m.width(out, S16) <= 119


def test_truncate_to_nothing(m: Measurer) -> None:
    assert m.truncate("Partner", S16, 3) == ""


def test_wrap_respects_lines_and_width(m: Measurer) -> None:
    text = "Svag vind från SO, 0,5 m/s med byar 1,5. Fukt 89 %, tryck 1010 hPa och sjunkande."
    lines = m.wrap(text, S16, 200, 3)
    assert len(lines) == 3
    assert all(m.width(line, S16) <= 199 for line in lines)
    assert lines[-1].endswith(ELLIPSIS)


def test_wrap_short_text_single_line(m: Measurer) -> None:
    assert m.wrap("Grått och uppehåll", S16, 400, 2) == ["Grått och uppehåll"]


def test_wrap_empty(m: Measurer) -> None:
    assert m.wrap("", S16, 100, 2) == []
