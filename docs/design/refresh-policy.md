# Refresh policy and night sleep (Sprint 03 T-07, 2026-11-08)

## What the device does (firmware 1.8.19 research notes; the owner runs 1.8.10)

- It wakes every `refresh_rate` seconds, calls `/api/display`, and **redraws only when
  `filename` changed**. paperboard's filename is the frame's content hash, so a quiet
  dashboard costs no panel refresh at all.
- **Refresh type:**
  - Full refresh (black/white flash, clears ghosting) every **8th** redraw, or always when
    `maximum_compatibility` is true. paperboard never sets that flag.
  - Partial refresh otherwise.
  - With `refresh_rate` ≥ 30 min, the firmware uses a fast full refresh instead of partial,
    against ghosting.
- **Battery:** the cost is per **wake** (Wi-Fi association, ~5 s awake; the owner's
  `Wake-Time` header shows ~5.4 s) plus per **redraw**. Wakes dominate.

## paperboard's levers

| Lever | Where | Effect |
|---|---|---|
| Content-hash filename | always on | No redraw (flash) unless something visible changed. The clock is bucketed by the layout's `clock_resolution` (default 5 min), so a ticking clock cannot force a redraw every wake. |
| Screen `refresh_rate` | screen config (default 900 s) | Wakes per day: 900 s → 96/day. |
| Schedule entry `refresh_rate` | schedule file | E.g. `{layout: natt, from: "22:00", to: "06:00", refresh_rate: 3600}`, 8 wakes overnight instead of 32. |
| Wake after a switch | automatic with schedules | The rate is shortened so the device wakes ~30 s after the next window boundary. The morning Tavlan appears at 07:00, not at 07:14. |

**Recommended night policy for battery panels:** a schedule entry from 22:00 to 06:00 with
`refresh_rate: 3600`, and a quiet layout (no clock, no hourly data), so overnight wakes almost
never redraw.

## Measuring it

- The **battery %** and **voltage** sensors (T-24 in Sprint 01) give the drain per day.
- **Last check-in** and **Missed check-in** show whether the device actually sleeps as told.

**The owner's device is USB-powered** (4.20 V on every check-in, T-04), so its battery impact
cannot be measured on it. The policy above is tested by schedule unit tests and the display
view; battery-life numbers need a battery panel and stay **unmeasured**.
