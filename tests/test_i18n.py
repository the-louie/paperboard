"""Every translated text table has the same keys in sv and en; layouts can pin a language."""

import datetime as dt
from zoneinfo import ZoneInfo

import custom_components.paperboard.widget_registry  # noqa: F401
from custom_components.paperboard import (
    widget_registry,
    widgets,
    widgets_agenda,
    widgets_almanac,
    widgets_flow,
    widgets_series,
    widgets_sky,
    widgets_text,
    widgets_values,
    widgets_weather,
)
from custom_components.paperboard.compose import render_spec
from custom_components.paperboard.fonts import load_fonts
from custom_components.paperboard.layout_file import parse
from custom_components.paperboard.layouts import Snapshot
from custom_components.paperboard.style import Theme
from custom_components.paperboard.text import Measurer

MODULES = (widget_registry, widgets, widgets_agenda, widgets_almanac, widgets_flow,
           widgets_series, widgets_sky, widgets_text, widgets_values, widgets_weather)


def test_sv_and_en_tables_match() -> None:
    checked = 0
    for module in MODULES:
        for name, value in vars(module).items():
            if isinstance(value, dict) and set(value) >= {"sv", "en"}:
                sv, en = value["sv"], value["en"]
                if isinstance(sv, dict):
                    assert set(sv) == set(en), f"{module.__name__}.{name}"
                elif isinstance(sv, list | tuple):
                    assert len(sv) == len(en), f"{module.__name__}.{name}"
                else:
                    assert isinstance(sv, str) and isinstance(en, str), name
                checked += 1
    assert checked >= 15


def test_layout_can_pin_language() -> None:
    spec = parse("name: x\nlang: en\ngrid: {columns: [fr], rows: [fr], areas: [a]}\n"
                 "widgets: [{type: header, area: a, options: {badge: none}}]\n", "x")
    snap = Snapshot(now=dt.datetime(2026, 11, 8, 12, tzinfo=ZoneInfo("Europe/Stockholm")),
                    width=800, height=480, screen_name="x", lang="sv")
    svg = render_spec(spec, snap, Measurer(load_fonts()), Theme())
    assert "Sunday 8 November" in svg and "Söndag" not in svg


def test_layout_text_per_language() -> None:
    from custom_components.paperboard.widget_registry import layout_text

    title = {"sv": "Vädret", "en": "Weather"}
    assert layout_text(title, "sv") == "Vädret"
    assert layout_text(title, "en") == "Weather"
    assert layout_text(title, "de") == "Weather"  # unknown language: English
    assert layout_text({"sv": "Bara svenska"}, "en") == "Bara svenska"
    assert layout_text("Plain", "en") == "Plain"
    assert layout_text(None, "en") is None
