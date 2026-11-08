"""Time-of-day schedules: a layout file with `schedule:` picks another layout per render.

```yaml
name: hallen_dag
schedule:
  - {layout: tavlan, from: "07:00", to: "08:00", days: weekdays, when: binary_sensor.skoldag}
  - {layout: tidslinjen, from: "08:00", to: "22:00"}
  - {layout: almanackan, from: "22:00", to: "07:00", refresh_rate: 3600}
default: tidslinjen
```

`when` (optional) must be 'on' for the entry to apply; an unavailable sensor does not match.
The device's refresh_rate is shortened so it wakes right after the next switch.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from .schema import vol

DAY_SETS = {"all": set(range(7)), "weekdays": set(range(5)), "weekend": {5, 6}}
DAY_NAMES = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _clock(value: Any) -> str:
    try:
        dt.time.fromisoformat(str(value))
    except ValueError as err:
        raise vol.Invalid("expected HH:MM") from err
    return str(value)


def _days(value: Any) -> list[int]:
    if isinstance(value, str) and value in DAY_SETS:
        return sorted(DAY_SETS[value])
    if isinstance(value, list) and all(isinstance(d, str) and d in DAY_NAMES for d in value):
        return sorted(DAY_NAMES[d] for d in value)
    raise vol.Invalid("expected all, weekdays, weekend or a list like [mon, tue]")


ENTRY = vol.Schema({
    vol.Required("layout"): str,
    vol.Optional("from", default="00:00"): _clock,
    vol.Optional("to", default="00:00"): _clock,
    vol.Optional("days", default="all"): _days,
    vol.Optional("when"): vol.All(str, vol.Match(r"^[a-z_]+\.[a-z0-9_]+$")),
    vol.Optional("refresh_rate"): vol.All(int, vol.Range(min=60, max=86_400)),
})
SCHEDULE = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Match(r"^[a-z0-9_]+$")),
    vol.Optional("title"): str,
    vol.Required("schedule"): vol.All([ENTRY], vol.Length(min=1)),
    vol.Required("default"): str,
})


@dataclass(frozen=True)
class Entry:
    layout: str
    start: dt.time
    end: dt.time
    days: frozenset[int]
    when: str | None
    refresh_rate: int | None

    def covers(self, now: dt.datetime, states: dict[str, dict[str, Any]]) -> bool:
        t, weekday = now.time(), now.weekday()
        if self.start <= self.end:
            inside = self.start <= t < self.end if self.start != self.end else True
            day = weekday
        else:  # crosses midnight: the early part belongs to the previous day's entry
            inside = t >= self.start or t < self.end
            day = weekday if t >= self.start else (weekday - 1) % 7
        if not inside or day not in self.days:
            return False
        return self.when is None or states.get(self.when, {}).get("state") == "on"


@dataclass(frozen=True)
class ScheduleSpec:
    name: str
    title: str
    entries: tuple[Entry, ...]
    default: str
    source: str

    @property
    def conditions(self) -> tuple[str, ...]:
        return tuple(e.when for e in self.entries if e.when)

    def active(self, now: dt.datetime, states: dict[str, dict[str, Any]]) -> Entry | None:
        return next((e for e in self.entries if e.covers(now, states)), None)

    def layout_at(self, now: dt.datetime, states: dict[str, dict[str, Any]]) -> str:
        entry = self.active(now, states)
        return entry.layout if entry else self.default

    def next_switch(self, now: dt.datetime) -> dt.datetime:
        """The next from/to boundary of any entry (conditions can only switch at them)."""
        candidates = []
        for e in self.entries:
            for t in (e.start, e.end):
                at = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                if at <= now:
                    at += dt.timedelta(days=1)
                candidates.append(at)
        return min(candidates) if candidates else now + dt.timedelta(days=1)

    def refresh_rate(self, now: dt.datetime, states: dict[str, dict[str, Any]],
                     base: int) -> int:
        entry = self.active(now, states)
        rate = entry.refresh_rate if entry and entry.refresh_rate else base
        until = int((self.next_switch(now) - now).total_seconds()) + 30
        return max(60, min(rate, until))


def parse_schedule(raw: dict[str, Any], source: str) -> ScheduleSpec:
    data = SCHEDULE(raw)
    entries = tuple(Entry(layout=e["layout"], start=dt.time.fromisoformat(e["from"]),
                          end=dt.time.fromisoformat(e["to"]), days=frozenset(e["days"]),
                          when=e.get("when"), refresh_rate=e.get("refresh_rate"))
                    for e in data["schedule"])
    return ScheduleSpec(name=data["name"], title=data.get("title", data["name"]),
                        entries=entries, default=data["default"], source=source)
