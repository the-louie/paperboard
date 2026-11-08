"""Display number formatting never raises and uses real typography."""

import pytest

from custom_components.paperboard.fmt import MISSING, number, signed, to_float, with_unit


@pytest.mark.parametrize("raw", [None, "unavailable", "unknown", "", "abc", float("nan"), True])
def test_garbage_is_missing(raw: object) -> None:
    assert to_float(raw) is None
    assert number(raw) == MISSING
    assert signed(raw) == MISSING
    assert with_unit(raw, "°") == MISSING


def test_decimal_comma_and_minus() -> None:
    assert number(3.14) == "3,1"
    assert number("-0.84") == "−0,8"
    assert number(-0.04) == "0,0"  # no "−0,0"
    assert number(3.1, 1, "en") == "3.1"
    assert number("3,5") == "3,5"


def test_signed() -> None:
    assert signed(1.2) == "+1,2"
    assert signed(-0.8) == "−0,8"
    assert signed(0.01) == "±0,0"


def test_units() -> None:
    assert with_unit(3.1, "°") == "3,1°"
    assert with_unit(89, "%", 0) == "89 %"
    assert with_unit(1.894, "kr", 2) == "1,89 kr"
