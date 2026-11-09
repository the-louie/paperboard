"""i18n core: catalogs, language resolution, lookup with fallbacks (docs/design/i18n.md)."""

from unittest.mock import patch

from custom_components.paperboard import i18n
from custom_components.paperboard.layout_file import parse
from custom_components.paperboard.layouts import Snapshot

CATALOGS = {"en": {"date": {"today": "Today", "weekday": ["Mon", "Tue"]},
                   "greet": "Hello {name}"},
            "sv": {"date": {"today": "Idag"}},
            "pt-BR": {"date": {"today": "Hoje"}}}


def test_resolution_exact_base_then_english() -> None:
    with patch.object(i18n, "_catalogs", CATALOGS):
        assert i18n.resolve("sv") == "sv"
        assert i18n.resolve("sv-SE") == "sv"
        assert i18n.resolve("en-GB") == "en"
        assert i18n.resolve("pt-BR") == "pt-BR"
        assert i18n.resolve("pt") == "en"
        assert i18n.resolve("de") == "en"
        assert i18n.resolve(None) == "en" and i18n.resolve("") == "en"


def test_lookup_falls_back_and_never_raises() -> None:
    with patch.object(i18n, "_catalogs", CATALOGS):
        assert i18n.t("sv", "date.today") == "Idag"
        assert i18n.t("de", "date.today") == "Today"
        assert i18n.tl("sv", "date.weekday") == ["Mon", "Tue"]  # missing in sv: English
        assert i18n.t("sv", "greet", name="Kim") == "Hello Kim"
        assert i18n.t("en", "greet") == "Hello {name}"  # no args: unformatted
        assert i18n.t("en", "greet", other=1) == "Hello {name}"  # wrong args: no exception
        assert i18n.t("en", "no.such.key") == "no.such.key"
        assert i18n.t("en", "date") == "date"  # a group, not a text
        assert i18n.tl("en", "no.such.list") == []


def test_shipped_catalogs_english_default() -> None:
    assert {"en", "sv"} <= set(i18n.available())
    assert Snapshot(now=None, width=1, height=1, screen_name="x").lang == "en"  # type: ignore[arg-type]
    assert i18n.t("en", "language.name") == "English"


def test_layout_pin_accepts_any_language_code() -> None:
    base = ("name: x\ngrid: {columns: [fr], rows: [fr], areas: [a]}\n"
            "widgets: [{type: header, area: a}]\n")
    for code in ("auto", "sv", "en", "pt-BR", "de"):
        assert parse(base + f"lang: {code}\n", "x.yaml").lang == code
    for bad in ("english", "s", "sv_SE!"):
        try:
            parse(base + f"lang: {bad}\n", "x.yaml")
        except Exception:
            continue
        raise AssertionError(bad)


def test_layout_text_from_a_catalog_key() -> None:
    from custom_components.paperboard.widget_registry import layout_text

    assert layout_text({"key": "section.home"}, "en") == "Home"
    assert layout_text({"key": "section.home"}, "sv") == "Hemmet"
    assert layout_text({"key": "section.home"}, "de") == "Home"
    assert layout_text({"key": "no.such"}, "en") == "no.such"  # visible, never an exception


def test_every_bundled_layout_has_a_display_name() -> None:
    from custom_components.paperboard.layout_file import load_all

    for name in load_all(None).layouts:
        for lang in i18n.available():
            assert i18n.t(lang, f"layout.{name}") != f"layout.{name}", (lang, name)


def test_numbers_follow_the_language() -> None:
    from custom_components.paperboard import fmt

    assert fmt.number(2.84) == "2.8"  # English default
    assert fmt.number(2.84, 1, "en") == "2.8" and fmt.number(2.84, 1, "sv") == "2,8"
    assert fmt.with_unit(-0.84, "°", 1, "sv") == "−0,8°"
    assert fmt.number(2.84, 1, "pt-BR") == "2,8"  # base language decides
    assert fmt.signed(1.25, 1, "en") == "+1.2" or fmt.signed(1.25, 1, "en") == "+1.3"


def test_english_is_british() -> None:
    """Owner 2026-11-09: British English is the default (colour, centre, grey, metre)."""
    import json
    import re
    from pathlib import Path

    base = Path(i18n.__file__).parent
    american = re.compile(r"\b(colors?|centers?|centered|gray|behaviors?|favorites?|"
                          r"customiz\w*|organiz\w*|prioritiz\w*|analyz\w*|catalogs?|dialogs?)\b",
                          re.I)
    product_names = {"Kobo Libra Color"}
    files = (base / "strings.json", base / "translations" / "en.json", base / "i18n" / "en.json")
    for path in files:
        text = json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False)
        for name in product_names:
            text = text.replace(name, "")
        hits = {m.group(0) for m in american.finditer(text)}
        assert not hits, (path.name, sorted(hits))
