"""Every bundled font loads and has its licence text."""

from custom_components.paperboard.fonts import FONT_DIR, FONT_FILES, PIXEL_FONT_SIZE, load_fonts


def test_all_fonts_load_in_pillow() -> None:
    reg = load_fonts()
    assert set(reg.data) == set(FONT_FILES)
    for family, weight in FONT_FILES:
        size = PIXEL_FONT_SIZE.get(family, 38)
        assert reg.pillow(family, weight, size).getlength("Söndag 3,1°") > 0


def test_licences_present() -> None:
    for name in ("LICENSES.md", "Inter-OFL.txt", "TRMNL-OFL.txt"):
        assert (FONT_DIR / name).read_text(encoding="utf-8").strip()
    assert "Open Font License" in (FONT_DIR / "TRMNL-OFL.txt").read_text(encoding="utf-8")
