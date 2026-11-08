"""Panel profiles from TRMNL's model registry (bundled models.json), chosen automatically from
the device's Model / Width / Height headers, or fixed by the screen config."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

MODELS_FILE = Path(__file__).parent / "models.json"
MAX_RENDER_DEPTH = 2  # this renderer emits 1- or 2-bit PNGs (4-bit: B-065)
DEFAULT = "og_png"


@dataclass(frozen=True)
class Profile:
    model: str
    width: int
    height: int
    bit_depth: int
    byte_limit: int
    scale_factor: float
    rotation: int


@cache
def _models() -> dict:
    return json.loads(MODELS_FILE.read_text(encoding="utf-8"))


def _profile(name: str) -> Profile:
    m = _models()["models"][name]
    return Profile(model=name, width=m["width"], height=m["height"],
                   bit_depth=min(m["bit_depth"], MAX_RENDER_DEPTH),
                   byte_limit=m["byte_limit"], scale_factor=m["scale_factor"],
                   rotation=m["rotation"])


def names() -> list[str]:
    return sorted(_models()["models"])


def resolve(model: str | None = None, width: int | None = None,
            height: int | None = None) -> Profile:
    """Registry name or firmware alias first, then a model with the reported size, else OG."""
    models = _models()
    name = models["firmware_aliases"].get(model or "", model)
    if name in models["models"]:
        return _profile(name)
    if width and height:
        same = [n for n, m in models["models"].items()
                if (m["width"], m["height"]) == (width, height)]
        if same:
            # Prefer TRMNL's own models, then the lowest depth (safest for unknown panels).
            same.sort(key=lambda n: (not n.startswith("og"), models["models"][n]["bit_depth"]))
            return _profile(same[0])
    return _profile(DEFAULT)
