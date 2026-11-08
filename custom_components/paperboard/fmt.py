"""Number formatting for the display: decimal comma, real minus sign, em dash for missing.

Every formatter accepts anything (state strings, None, "unavailable") and never raises:
a value that cannot be read as a number renders as MISSING.
"""

from __future__ import annotations

import math

MISSING = "—"
MINUS = "−"  # U+2212
PLUS_MINUS = "±"

_COMMA_LANGS = {"sv", "de", "fr", "nb", "nn", "da", "fi", "nl", "es", "it", "pt", "pl", "cs"}


def to_float(value: object) -> float | None:
    """A finite float, or None for missing/unknown/unavailable/garbage."""
    if value is None or isinstance(value, bool):
        return None
    try:
        num = float(str(value).replace(",", ".").replace(MINUS, "-"))
    except ValueError:
        return None
    return num if math.isfinite(num) else None


def decimal_sep(lang: str) -> str:
    return "," if lang.split("-")[0].lower() in _COMMA_LANGS else "."


def number(value: object, decimals: int = 1, lang: str = "sv") -> str:
    """'3,1' / '−0,8' / '—'."""
    num = to_float(value)
    if num is None:
        return MISSING
    text = f"{abs(num):.{decimals}f}".replace(".", decimal_sep(lang))
    if num < 0 and float(text.replace(",", ".")) != 0:
        return MINUS + text
    return text


def signed(value: object, decimals: int = 1, lang: str = "sv") -> str:
    """'+1,2' / '−0,8' / '±0,0' / '—'."""
    num = to_float(value)
    if num is None:
        return MISSING
    body = number(abs(num), decimals, lang)
    if float(body.replace(",", ".")) == 0:
        return PLUS_MINUS + body
    return ("+" if num > 0 else MINUS) + body


def with_unit(value: object, unit: str, decimals: int = 1, lang: str = "sv") -> str:
    """'3,1°' (no space for °), '89 %', '1,89 kr', or '—' with no unit."""
    text = number(value, decimals, lang)
    if text == MISSING:
        return MISSING
    return f"{text}{unit}" if unit == "°" else f"{text} {unit}"
