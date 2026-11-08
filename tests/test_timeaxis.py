"""Shared time axis maths."""

import datetime as dt
from zoneinfo import ZoneInfo

from custom_components.paperboard.timeaxis import TimeAxis

TZ = ZoneInfo("Europe/Stockholm")
NOW = dt.datetime(2026, 11, 8, 12, 15, tzinfo=TZ)


def test_mapping_and_slots() -> None:
    axis = TimeAxis.from_now(NOW, 24, 286, 790)
    assert axis.start.hour == 12 and axis.px_per_hour == 21
    assert axis.x(axis.start) == 286 and axis.x(axis.end) == 790
    assert axis.slot(NOW) == (286, 307)
    assert axis.slot(NOW - dt.timedelta(hours=1)) is None
    assert [t.hour for _, t in axis.ticks(6)] == [12, 18, 0, 6]


def test_two_widgets_same_axis_same_x() -> None:
    a = TimeAxis.from_now(NOW, 24, 286, 790)
    b = TimeAxis.from_now(NOW.replace(minute=59), 24, 286, 790)
    t = NOW + dt.timedelta(hours=5, minutes=30)
    assert a.x(t) == b.x(t)


def test_spans_are_clipped() -> None:
    axis = TimeAxis.from_now(NOW, 24, 0, 240)
    night = (dt.datetime(2026, 11, 8, 16, 3, tzinfo=TZ), dt.datetime(2026, 11, 9, 7, 31, tzinfo=TZ))
    old = (dt.datetime(2026, 11, 7, 16, tzinfo=TZ), dt.datetime(2026, 11, 8, 7, tzinfo=TZ))
    edge = (dt.datetime(2026, 11, 9, 10, tzinfo=TZ), dt.datetime(2026, 11, 9, 14, tzinfo=TZ))
    late = (dt.datetime(2026, 11, 9, 16, tzinfo=TZ), dt.datetime(2026, 11, 10, 7, tzinfo=TZ))
    spans = axis.spans([old, night, edge, late])
    assert spans == [(axis.x(night[0]), axis.x(night[1])), (axis.x(edge[0]), 240)]
