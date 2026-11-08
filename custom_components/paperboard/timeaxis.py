"""One shared time scale, so price, expected solar and temperature line up (owner rule)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeAxis:
    """`hours` whole hours from `start` (floored to the hour), drawn between x0 and x1."""

    start: dt.datetime
    hours: int
    x0: float
    x1: float

    @classmethod
    def from_now(cls, now: dt.datetime, hours: int, x0: float, x1: float) -> TimeAxis:
        return cls(now.replace(minute=0, second=0, microsecond=0), hours, x0, x1)

    @property
    def end(self) -> dt.datetime:
        return self.start + dt.timedelta(hours=self.hours)

    @property
    def px_per_hour(self) -> float:
        return (self.x1 - self.x0) / self.hours

    def x(self, t: dt.datetime) -> float:
        return self.x0 + (t - self.start).total_seconds() / 3600 * self.px_per_hour

    def clamp(self, x: float) -> float:
        return min(max(x, self.x0), self.x1)

    def contains(self, t: dt.datetime) -> bool:
        return self.start <= t < self.end

    def slot(self, t: dt.datetime) -> tuple[float, float] | None:
        """x-range of the whole hour containing t, or None outside the axis."""
        if not self.contains(t):
            return None
        hour = t.replace(minute=0, second=0, microsecond=0)
        return self.x(hour), self.x(hour + dt.timedelta(hours=1))

    def ticks(self, every: int = 3) -> list[tuple[float, dt.datetime]]:
        return [(self.x(self.start + dt.timedelta(hours=h)), self.start + dt.timedelta(hours=h))
                for h in range(0, self.hours, every)]

    def spans(self, intervals: list[tuple[dt.datetime, dt.datetime]]
              ) -> list[tuple[float, float]]:
        """Clipped x-ranges of time intervals (e.g. nights) that overlap the axis."""
        out = []
        for a, b in intervals:
            if b <= self.start or a >= self.end:
                continue
            out.append((self.clamp(self.x(a)), self.clamp(self.x(b))))
        return out
