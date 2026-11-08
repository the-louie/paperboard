"""Layout files: YAML -> validated LayoutSpec. Reading is blocking: call from an executor.

Bundled layouts ship in layouts_yaml/; the user's own in /config/paperboard/ win on a name
clash. A file that fails validation never replaces the last good version of that layout; its
errors are returned so the hub can raise a Repairs issue (docs/design/layout-schema.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .grid import Grid, GridError
from .schema import format_errors, vol

BUNDLED_DIR = Path(__file__).parent / "layouts_yaml"
WIDGET_TYPES = ("header", "now", "timeline", "hourly_table", "daily", "energy", "energy_flow",
                "rooms", "stat", "sun_moon", "agenda", "text", "footer", "hourly_strip",
                "tomorrow", "date", "week", "now_grid")
COLLAPSE = ("left", "right", "up", "down", "none")
FRAMES = ("none", "box", "rounded", "inverted", "panel")


def _track(value: Any) -> int | str:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"\d*(\.\d+)?fr", value.strip()):
        return value.strip()
    raise vol.Invalid("expected px (int) or 'fr'")


WIDGET = vol.Schema({
    vol.Required("type"): vol.In(WIDGET_TYPES),
    vol.Required("area"): str,
    vol.Optional("options", default={}): dict,
    vol.Optional("collapse"): vol.In(COLLAPSE),
    vol.Optional("height"): vol.All(int, vol.Range(min=10)),  # px share when stacked
})
LAYOUT = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Match(r"^[a-z0-9_]+$")),
    vol.Optional("title"): str,
    vol.Optional("canvas", default=[800, 480]): vol.All([vol.All(int, vol.Range(min=1))],
                                                         vol.Length(min=2, max=2)),
    vol.Required("grid"): {
        vol.Required("columns"): vol.All([_track], vol.Length(min=1)),
        vol.Required("rows"): vol.All([_track], vol.Length(min=1)),
        vol.Required("areas"): vol.All([str], vol.Length(min=1)),
        vol.Optional("rules", default=2): vol.All(int, vol.Range(min=0, max=8)),
        vol.Optional("padding", default=[8, 16]): vol.All([vol.All(int, vol.Range(min=0))],
                                                          vol.Length(min=2, max=2)),
        vol.Optional("gap", default=0): vol.All(int, vol.Range(min=0, max=40)),
        vol.Optional("margin", default=0): vol.All(int, vol.Range(min=0, max=40)),
        vol.Optional("frames", default={}): {str: vol.In(FRAMES)},
        vol.Optional("paddings", default={}): {str: vol.All([vol.All(int, vol.Range(min=0))],
                                                            vol.Length(min=2, max=2))},
    },
    vol.Required("widgets"): vol.All([WIDGET], vol.Length(min=1)),
    vol.Optional("clock_resolution", default=300): vol.All(int, vol.Range(min=60)),
    vol.Optional("lang", default="auto"): vol.In(("auto", "sv", "en")),
})


@dataclass(frozen=True)
class LayoutSpec:
    name: str
    title: str
    canvas: tuple[int, int]
    grid: dict[str, Any]
    widgets: tuple[dict[str, Any], ...]
    clock_resolution: int
    lang: str
    source: str  # file path, for messages


@dataclass
class LoadResult:
    layouts: dict[str, LayoutSpec] = field(default_factory=dict)
    errors: dict[str, list[str]] = field(default_factory=dict)  # file -> messages
    mtimes: dict[str, tuple[int, int]] = field(default_factory=dict)  # (mtime_ns, size)


def parse(text: str, source: str) -> LayoutSpec:  # or a ScheduleSpec for schedule files
    """Validate one file's text; raises ValueError with all messages joined by newlines."""
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as err:
        raise ValueError(f"YAML: {err}") from err
    if not isinstance(raw, dict):
        raise ValueError("the file must be a mapping with name, grid and widgets")
    if "schedule" in raw:
        from .schedule import parse_schedule

        try:
            return parse_schedule(raw, source)  # type: ignore[return-value]
        except vol.Invalid as err:
            raise ValueError("\n".join(format_errors(err))) from err
    try:
        data = LAYOUT(raw)
    except vol.Invalid as err:
        raise ValueError("\n".join(format_errors(err))) from err
    g = data["grid"]
    try:
        m = g["margin"]
        grid = Grid.build(g["columns"], g["rows"], g["areas"], data["canvas"][0] - 2 * m,
                          data["canvas"][1] - 2 * m, g["gap"])
    except GridError as err:
        raise ValueError(f"grid: {err}") from err
    names = set(grid.names())
    bad = [f"widgets[{i}].area: unknown area {w['area']!r}"
           for i, w in enumerate(data["widgets"]) if w["area"] not in names]
    bad += [f"grid.frames.{a}: unknown area" for a in g["frames"] if a not in names]
    bad += [f"grid.paddings.{a}: unknown area" for a in g["paddings"] if a not in names]
    if bad:
        raise ValueError("\n".join(bad))
    return LayoutSpec(name=data["name"], title=data.get("title", data["name"]),
                      canvas=tuple(data["canvas"]), grid=g, widgets=tuple(data["widgets"]),
                      clock_resolution=data["clock_resolution"], lang=data["lang"],
                      source=source)


def load_all(user_dir: Path | None, previous: LoadResult | None = None) -> LoadResult:
    """Read bundled then user layouts. Invalid files keep the previous good spec, if any."""
    result = LoadResult()
    files = sorted(BUNDLED_DIR.glob("*.yaml"))
    if user_dir is not None and user_dir.is_dir():
        files += sorted(user_dir.glob("*.yaml"))
    for path in files:
        st = path.stat()
        result.mtimes[str(path)] = (st.st_mtime_ns, st.st_size)
        try:
            spec = parse(path.read_text(encoding="utf-8"), str(path))
        except (OSError, ValueError) as err:
            result.errors[str(path)] = str(err).splitlines()
            if previous:
                for name, spec_prev in previous.layouts.items():
                    if spec_prev.source == str(path):
                        result.layouts[name] = spec_prev
            continue
        result.layouts[spec.name] = spec
    # A schedule may only name layouts that exist (checked after all files are read).
    for name, spec in list(result.layouts.items()):
        targets = [e.layout for e in getattr(spec, "entries", ())]
        if hasattr(spec, "entries"):
            targets.append(spec.default)
            from .layouts import LAYOUTS as CODE_LAYOUTS

            missing = [t for t in targets
                       if t == name or (t not in result.layouts and t not in CODE_LAYOUTS)]
            if missing:
                result.errors[spec.source] = [f"schedule: unknown layout {t!r}" for t in missing]
                del result.layouts[name]
    return result


def changed(user_dir: Path | None, last: LoadResult) -> bool:
    """True when any layout file was added, removed or modified (cheap stat calls)."""
    files = list(BUNDLED_DIR.glob("*.yaml"))
    if user_dir is not None and user_dir.is_dir():
        files += list(user_dir.glob("*.yaml"))
    current = {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in files}
    return current != last.mtimes
