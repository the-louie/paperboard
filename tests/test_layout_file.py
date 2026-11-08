"""Layout file parsing, validation messages, last-good retention."""

from pathlib import Path

import pytest

from custom_components.paperboard import layout_file
from custom_components.paperboard.layout_file import changed, load_all, parse

GOOD = """
name: demo
grid:
  columns: [250, fr]
  rows: [40, fr]
  areas:
    - header header
    - now    timeline
widgets:
  - {type: header, area: header}
  - {type: now, area: now, collapse: right}
  - {type: timeline, area: timeline, options: {hours: 24}}
"""


def test_parse_good() -> None:
    spec = parse(GOOD, "x")
    assert spec.name == "demo" and spec.canvas == (800, 480)
    assert spec.grid["rules"] == 2 and len(spec.widgets) == 3


@pytest.mark.parametrize(("text", "message"), [
    ("[1, 2]", "must be a mapping"),
    ("name: Demo!\ngrid: {columns: [fr], rows: [fr], areas: [a]}\nwidgets: [{type: now, area: a}]",
     "name"),
    (GOOD.replace("type: now", "type: clock"), "widgets[1].type"),
    (GOOD.replace("area: timeline,", "area: nowhere,"), "unknown area 'nowhere'"),
    (GOOD.replace("columns: [250, fr]", "columns: [250, auto]"), "grid.columns[1]"),
    (GOOD.replace("- now    timeline", "- now"), "grid:"),
    ("name: x\n  bad: [", "YAML"),
])
def test_parse_errors(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message.replace("[", r"\[").replace("]", r"\]")):
        parse(text, "x")


def test_user_dir_wins_and_bad_file_keeps_last_good(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(layout_file, "BUNDLED_DIR", tmp_path / "bundled")
    (tmp_path / "bundled").mkdir()
    user = tmp_path / "user"
    user.mkdir()
    (user / "demo.yaml").write_text(GOOD)
    first = load_all(user)
    assert "demo" in first.layouts and not first.errors
    assert not changed(user, first)

    (user / "demo.yaml").write_text(GOOD.replace("type: now", "type: clock"))
    assert changed(user, first)
    second = load_all(user, previous=first)
    assert second.layouts["demo"] is first.layouts["demo"]  # last good kept
    assert any("widgets[1].type" in m for m in second.errors[str(user / "demo.yaml")])
