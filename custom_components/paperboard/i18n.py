"""Texts drawn into the image, per language (docs/design/i18n.md).

`i18n/en.json` is the source of truth; every other `i18n/<lang>.json` has the same keys.
Home Assistant's own UI texts stay in strings.json / translations/ (HA's mechanism).

Lookup never raises: a key missing in a language falls back to English, a key missing in
English shows the key itself, so a partial translation can never blank a screen.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

I18N_DIR = Path(__file__).parent / "i18n"
DEFAULT_LANG = "en"

_catalogs: dict[str, dict[str, Any]] | None = None


def load_catalogs() -> dict[str, dict[str, Any]]:
    """Read every catalog once. Blocking file I/O: call it in the executor first (setup does);
    later calls return the cache."""
    global _catalogs
    if _catalogs is None:
        _catalogs = {p.stem: json.loads(p.read_text(encoding="utf-8"))
                     for p in sorted(I18N_DIR.glob("*.json"))}
    return _catalogs


def available() -> list[str]:
    return sorted(load_catalogs())


def resolve(language: str | None) -> str:
    """HA's language ("en-GB", "sv", "pt-BR") -> a catalog: exact, then base, then English."""
    catalogs = load_catalogs()
    lang = (language or "").strip().replace("_", "-")
    for candidate in (lang, lang.split("-")[0].lower()):
        if candidate and candidate in catalogs:
            return candidate
    return DEFAULT_LANG


def _lookup(catalog: dict[str, Any], key: str) -> Any:
    node: Any = catalog
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def get(lang: str, key: str) -> Any:
    """The raw value (string, list or dict) for a key, with the English fallback."""
    catalogs = load_catalogs()
    for source in (lang, DEFAULT_LANG):
        value = _lookup(catalogs.get(source, {}), key)
        if value is not None:
            return value
    return None


def t(lang: str, key: str, **kw: Any) -> str:
    """One text, placeholders filled with str.format; the key itself when nothing is found."""
    value = get(lang, key)
    if not isinstance(value, str):
        return key
    try:
        return value.format(**kw) if kw else value
    except (KeyError, IndexError, ValueError):
        return value


def tl(lang: str, key: str) -> list[str]:
    """A list of texts (weekday or month names); English when the language lacks it."""
    value = get(lang, key)
    if isinstance(value, list) and value:
        return [str(v) for v in value]
    english = _lookup(load_catalogs().get(DEFAULT_LANG, {}), key)
    return [str(v) for v in english] if isinstance(english, list) else []
