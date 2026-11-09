"""Calendar agenda (mockup 07): events grouped per day, truncated by measured width."""

from __future__ import annotations

import datetime as dt

from .layouts import Snapshot
from .style import Theme
from .svg import Svg
from .text import Measurer
from .widgets import Rect

DAY = {"sv": ["mån", "tis", "ons", "tor", "fre", "lör", "sön"],
       "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
HOLIDAY_SV = {"Father's Day": "Fars dag", "Mother's Day": "Mors dag",
              "Christmas Eve": "Julafton", "Christmas Day": "Juldagen",
              "New Year's Eve": "Nyårsafton", "New Year's Day": "Nyårsdagen",
              "Midsummer Eve": "Midsommarafton", "Midsummer Day": "Midsommardagen",
              "Easter Sunday": "Påskdagen", "Good Friday": "Långfredagen",
              "National Day of Sweden": "Sveriges nationaldag",
              "All Saints' Day": "Alla helgons dag"}


WORDS = {"sv": {"today": "Idag", "tomorrow": "Imorgon", "none": "Inga händelser",
                "title": "KALENDER", "all_day": "heldag"},
         "en": {"today": "Today", "tomorrow": "Tomorrow", "none": "No events",
                "title": "CALENDAR", "all_day": "all day"}}


def _start(ev: dict, tz: dt.tzinfo) -> dt.datetime | None:
    try:
        raw = str(ev["start"])
        if len(raw) == 10:
            return dt.datetime.fromisoformat(raw).replace(tzinfo=tz)
        return dt.datetime.fromisoformat(raw).astimezone(tz)
    except (KeyError, ValueError, TypeError):
        return None


def agenda(svg: Svg, r: Rect, snap: Snapshot, measure: Measurer, theme: Theme, days: int = 7,
           title: bool = True) -> bool:
    cals = [c for c in (snap.roles.get("calendars") or []) if isinstance(c, str)]
    if not cals:
        return False
    tz = snap.now.tzinfo
    words = WORDS.get(snap.lang, WORDS["en"])
    end = snap.now + dt.timedelta(days=days)
    items = []
    for cal in cals:
        for ev in snap.events.get(cal, []):
            if not isinstance(ev, dict) or (start := _start(ev, tz)) is None:
                continue
            if start.date() >= snap.now.date() and start < end:
                summary = str(ev.get("summary", ""))
                if snap.lang == "sv":
                    summary = HOLIDAY_SV.get(summary, summary)
                items.append((start, bool(ev.get("all_day")), summary))
    items.sort(key=lambda i: (i[0].date(), not i[1], i[0]))
    p = theme.px
    y = r.y
    head, body, bold = theme.text("xs", bold=True), theme.text("s"), theme.text("s", bold=True)
    if title:
        svg.text(r.x, y + p(12), words["title"], head)
        y += p(20)
    if not items:
        svg.text(r.x, y + p(14), words["none"], body)
        return True
    current = None
    for start, all_day, summary in items:
        day = start.date()
        if day != current:
            if y + p(34) > r.y + r.h:
                break
            current = day
            delta = (day - snap.now.date()).days
            label = words["today"] if delta == 0 else words["tomorrow"] if delta == 1 else \
                f"{DAY[snap.lang][day.weekday()]} {day.day}/{day.month}"
            svg.text(r.x, y + p(13), label, head)
            svg.line(r.x, y + p(16), r.x + r.w, y + p(16), 1)
            y += p(20)
        if y + p(18) > r.y + r.h:
            break
        when = words["all_day"] if all_day else f"{start:%H:%M}"
        # "heldag" is in xs, which on big panels snaps to the same pixel size as s.
        tw = max(measure.width("00:00 ", bold),
                 measure.width(f"{words['all_day']} ", theme.text("xs")))
        svg.text(r.x, y + p(13), when, bold if not all_day else theme.text("xs"))
        svg.text(r.x + tw, y + p(13), measure.truncate(summary, body, r.w - tw), body)
        y += p(18)
    return True
