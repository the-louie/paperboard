# Sprint 02 — Layout engine and the hard widgets: mockup 01 from YAML on real data
**Status:** done (closed 2026-11-08)
**Current ticket:** —
**Last completed:** T-26 (`done` — commit `43d2193`)
**Budget:** 86h estimated (band 80–120h)

## Goal
Replace hand-built SVG with YAML grid layouts that bind roles to entities, plus the widgets the
owner's mockups need: the shared time axis (price and expected solar), the daily forecast
with warning inversion, the hourly table, energy flow, rooms, and sun/moon.

## Demo
- `tidslinjen.yaml`, with the owner's changes, rendered from the owner's fixture through
  roles (golden PNG). The price and solar charts share one x-axis.
- The same layout rendered with **zero entities** passes the empty-house gate.
- A 2-bit render of the same layout.

## Tickets
| ID | Title | Est h | Deps | From | Status | Notes |
|---|---|---|---|---|---|---|
| T-01 | Research: schema library for layouts | 2 | — | B-027 | done | Landed in 2113c43 |
| T-02 | Design: layout YAML schema | 4 | T-01 | B-028 | done | Landed in 6dfdd46 |
| T-03 | Type scale and style tokens | 3 | T-02 | B-031 | done | Landed in f96414d |
| T-04 | Grid engine with reflow | 5 | T-02 | B-030 | done | Landed in e3ca498 |
| T-05 | Layout loader and validation | 4 | T-02 | B-029 | done | Landed in bc57d71 |
| T-06 | Roles: binding in config/options flow | 5 | T-02 | B-032 | done | Landed in 32c21ff |
| T-07 | Repairs for missing entities | 3 | T-06 | B-033 | done | Landed in f0e2b6b |
| T-08 | Data: weather forecasts | 3 | — | B-034 | done | Landed in 792ce28 |
| T-09 | Research: price sources | 2 | — | B-035 | done | Landed in c4794bf |
| T-10 | Price adapters | 4 | T-09 | B-036 | done | Landed in ac5c7f8 |
| T-11 | Research: solar forecast source | 2 | — | B-037 | done | Landed in 7764679 |
| T-12 | Solar forecast adapter | 3 | T-11 | B-038 | done | Landed in 64c999f |
| T-13 | TimeAxis object | 3 | T-04 | B-039 | done | Landed in d9bca94 |
| T-14 | Weather icon set | 3 | T-03 | B-044 | done | Landed in b1e3ac8 |
| T-15 | Widget: price chart | 4 | T-10, T-13 | B-040 | done | Landed in 60e1bf4 |
| T-16 | Widget: solar forecast chart | 3 | T-12, T-13 | B-041 | done | Landed in 634eb68 |
| T-17 | Widget: daily forecast with warning inversion | 4 | T-08, T-14 | B-043 | done | Landed in f050b1a |
| T-18 | Widget: hourly table (Tavlan) | 4 | T-08, T-10, T-14 | B-042 | done | Landed in 45fc46d |
| T-19 | Widget: stat / key-value | 3 | T-03 | B-051 | done | Landed in 9b2d5aa |
| T-20 | Widget: room list | 2 | T-03 | B-048 | done | Landed in 4d5298c |
| T-21 | Widget: energy flow | 5 | T-03, T-06 | B-047 | done | Landed in be03364 |
| T-22 | Widget: sun and moon | 2 | T-03 | B-050 | done | Landed in e17c280 |
| T-23 | "Empty house" gate | 2 | T-04, T-15 | B-045 | done | Landed in 65b5261 |
| T-24 | Layout 01 Tidslinjen with the owner's changes | 3 | T-05, T-06, T-15, T-16, T-17 | B-046 | done | Landed in a7209a7 |
| T-25 | Panel profiles from the TRMNL model table | 4 | — | B-064 | done | Landed in 60c4770 |
| T-26 | 2-bit and 4-bit render paths | 4 | T-25 | B-065 | done | Landed in 43d2193 |

## Scope changes
- None pulled in. Discovered work went to the backlog: B-083 (scale YAML layouts for large panels). T-23 grew to include the layout composer and widget registry (~4 h against an estimate of 2 h), because the gate needs something to render with; T-24 would otherwise have built it.

## Retro
**Shipped (26/26 tickets, 181 tests, ruff clean):**
- **Layout engine:**
  - YAML spec plus loader (probatio/voluptuous, path-precise errors).
  - Repairs issue per broken file; the last good layout is kept.
  - Grid engine with reflow and merged rules.
  - Type scale (pixel fonts kept at native sizes), 1/2/4-bit style tokens.
  - Composer with an isolated widget registry (12 types).
- **Roles:**
  - Options-flow menu with 15 single roles and 2 list roles, all optional.
  - Repairs issue for a bound entity that disappears, after a 2-minute startup grace.
- **Data:**
  - Weather forecasts through `weather.get_forecasts`.
  - Prices: HACS nordpool, core nordpool service, ENTSO-e and float lists.
  - Solar forecast through the energy-platform contract of the bound sensor's integration.
  - Sun times from HA's astral helper.
- **Widgets:**
  - Shared TimeAxis.
  - Price chart: filled cheapest window, bracket, "tomorrow due" note.
  - Solar chart: hatched estimate, "förväntat idag / kvar".
  - Night shading.
  - Daily forecast with inverted warning days.
  - Hourly table.
  - Energy rows, stat, rooms.
  - Energy flow with figures beside the nodes.
  - Sun and moon, header, now, footer.
- **Profiles:** 58 TRMNL models plus the owner's XIAO alias; "auto" follows the device.
- **Gate:** every widget × {empty, garbage} × {1, 2-bit}, and every bundled layout, with zero
  exceptions. It caught 4 real crashes on garbage data the day it was added.
- **Demo:** `tidslinjen.yaml` on the owner's data through roles. Goldens at 1/2/4-bit; the
  1-bit frame is ~7 kB. Copies are in `<the maintainer's file share>`.
- **End to end in HA:** a screen on the bundled layout renders live through roles.

**Not shipped:** nothing.

**Estimate accuracy:** 86 h estimated, all 26 closed. T-23 ran ~2 h over (composer), absorbed
by T-24 needing less. The research tickets (T-01, T-09, T-11) came in at estimate.

**Findings worth keeping:**
1. **Solar forecast:** the owner's Energy-dashboard forecast link is broken (B-081 / H-54).
   The demo's hourly solar curve is test data until the owner relinks it; the total is real.
2. **Options-flow tests:** they must wait for the scheduled reload, or they flake on teardown
   (fixed twice, now the pattern).
3. **Device model string:** the owner's device reports `xiao_epaper_display`, which is not in
   TRMNL's registry. An alias and the size fallback cover it.

**What to change:**
- Sprint 03 builds the remaining layouts (02, 03, 05, 06, 07, 08), the calendar agenda
  (headers need calendar data for flags in production), text slots and the schedule.
- Production deploy (B-025) still waits on the owner.

