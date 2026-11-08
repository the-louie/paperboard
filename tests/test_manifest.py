"""Sanity checks on the integration's packaging metadata."""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_manifest_has_hacs_required_keys() -> None:
    manifest = json.loads((ROOT / "custom_components/paperboard/manifest.json").read_text())
    for key in ("domain", "documentation", "issue_tracker", "codeowners", "name", "version"):
        assert manifest[key], key
    assert manifest["domain"] == "paperboard"
    assert not any(r.lower().startswith("pillow") for r in manifest["requirements"])


def test_hacs_json_minimum_version() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert hacs["homeassistant"] >= "2026.3.0"


def test_brand_images() -> None:
    from PIL import Image

    brand = ROOT / "custom_components/paperboard/brand"
    assert Image.open(brand / "icon.png").size == (256, 256)
    assert Image.open(brand / "icon@2x.png").size == (512, 512)
    w, h = Image.open(brand / "logo.png").size
    assert 128 <= min(w, h) <= 256
