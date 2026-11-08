"""Price series from any supported source (docs/design/data-sources.md). Pure functions."""

from __future__ import annotations

import datetime as dt
import itertools
from dataclasses import dataclass, field
from typing import Any

from .fmt import to_float


@dataclass(frozen=True)
class PricePoint:
    start: dt.datetime
    end: dt.datetime
    value: float


@dataclass(frozen=True)
class PriceSeries:
    points: tuple[PricePoint, ...] = ()
    unit: str = ""
    includes_fees: bool | None = None
    tomorrow_expected_at: str | None = None
    current: float | None = None

    def hourly(self) -> list[PricePoint]:
        """Average finer points into whole hours (display resolution)."""
        buckets: dict[dt.datetime, list[float]] = {}
        for p in self.points:
            buckets.setdefault(p.start.replace(minute=0, second=0, microsecond=0),
                               []).append(p.value)
        return [PricePoint(h, h + dt.timedelta(hours=1), sum(v) / len(v))
                for h, v in sorted(buckets.items())]

    def cheapest_window(self, hours: int, after: dt.datetime) -> tuple[dt.datetime, float] | None:
        """Start and mean price of the cheapest run of `hours` whole hours from `after` on."""
        hourly = [p for p in self.hourly() if p.end > after]
        best: tuple[dt.datetime, float] | None = None
        for i in range(len(hourly) - hours + 1):
            run = hourly[i:i + hours]
            if any(b.start != a.end for a, b in itertools.pairwise(run)):
                continue  # not contiguous
            mean = sum(p.value for p in run) / hours
            if best is None or mean < best[1]:
                best = (run[0].start, mean)
        return best


def _parse_time(value: Any) -> dt.datetime | None:
    if isinstance(value, dt.datetime):
        return value
    try:
        return dt.datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _from_dicts(items: Any, start_key: str, end_key: str | None,
                value_key: str, scale: float) -> list[PricePoint]:
    rows = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        start, value = _parse_time(item.get(start_key)), to_float(item.get(value_key))
        if start is None or value is None:
            continue
        rows.append((start, _parse_time(item.get(end_key)) if end_key else None, value * scale))
    rows.sort(key=lambda r: r[0])
    points = []
    for i, (start, end, value) in enumerate(rows):
        if end is None:
            end = rows[i + 1][0] if i + 1 < len(rows) else (
                start + (rows[i][0] - rows[i - 1][0] if i else dt.timedelta(hours=1)))
        points.append(PricePoint(start, end, value))
    return points


def _from_floats(values: Any, day_start: dt.datetime, scale: float) -> list[PricePoint]:
    nums = [to_float(v) for v in values] if isinstance(values, list) else []
    if not nums or len([n for n in nums if n is not None]) != len(nums):
        return []
    step = dt.timedelta(days=1) / len(nums)
    return [PricePoint(day_start + i * step, day_start + (i + 1) * step, n * scale)
            for i, n in enumerate(nums)]


def from_state(state: dict[str, Any] | None, now: dt.datetime) -> PriceSeries:
    """Adapter for entities that carry their prices in attributes. Never raises."""
    if not state:
        return PriceSeries()
    attrs = state.get("attributes", {}) or {}
    scale = 0.01 if attrs.get("price_in_cents") else 1.0
    unit = str(attrs.get("unit_of_measurement") or "")
    current = to_float(state.get("state"))
    current = current * scale if current is not None else None
    points: list[PricePoint] = []
    nordpool_like = "raw_today" in attrs or "today" in attrs
    if "raw_today" in attrs:
        for key in ("raw_today", "raw_tomorrow"):
            points += _from_dicts(attrs.get(key), "start", "end", "value", scale)
    elif "today" in attrs:
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        points += _from_floats(attrs.get("today"), midnight, scale)
        if attrs.get("tomorrow_valid", True):
            points += _from_floats(attrs.get("tomorrow"), midnight + dt.timedelta(days=1), scale)
    elif isinstance(attrs.get("prices_today"), list) or isinstance(attrs.get("prices"), list):
        for key in ("prices_today", "prices_tomorrow", "prices"):
            points += _from_dicts(attrs.get(key), "time", None, "price", scale)
    dedup = {p.start: p for p in points}
    return PriceSeries(points=tuple(sorted(dedup.values(), key=lambda p: p.start)), unit=unit,
                       includes_fees=True if nordpool_like else None,
                       tomorrow_expected_at="13:00" if nordpool_like else None,
                       current=current)


def from_service(response: dict[str, list[dict[str, Any]]], area: str | None,
                 currency: str) -> PriceSeries:
    """Core nordpool get_prices_for_date responses (one or more days merged): MWh -> kWh."""
    rows: list[dict[str, Any]] = []
    for key, items in (response or {}).items():
        if area is None or key == area:
            rows += items or []
    points = _from_dicts(rows, "start", "end", "price", 1 / 1000)
    return PriceSeries(points=tuple(points), unit=f"{currency}/kWh", includes_fees=False,
                       tomorrow_expected_at="13:00")


@dataclass
class PriceSnapshot:
    """Plain-data form for the render snapshot."""

    points: list[tuple[str, str, float]] = field(default_factory=list)
    unit: str = ""
    includes_fees: bool | None = None
    tomorrow_expected_at: str | None = None
    current: float | None = None

    @classmethod
    def of(cls, series: PriceSeries) -> PriceSnapshot:
        return cls([(p.start.isoformat(), p.end.isoformat(), p.value) for p in series.points],
                   series.unit, series.includes_fees, series.tomorrow_expected_at,
                   series.current)

    def series(self) -> PriceSeries:
        return PriceSeries(tuple(PricePoint(dt.datetime.fromisoformat(s),
                                            dt.datetime.fromisoformat(e), v)
                                 for s, e, v in self.points),
                           self.unit, self.includes_fees, self.tomorrow_expected_at,
                           self.current)
