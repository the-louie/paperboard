# Sprint 02 — Layout engine and the hard widgets: mockup 01 from YAML on real data
**Status:** in progress (opened 2026-11-08)
**Current ticket:** T-16 (`todo` — Widget: solar forecast chart)
**Last completed:** T-15 (`done` — commit `60e1bf4`)
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
| T-16 | Widget: solar forecast chart | 3 | T-12, T-13 | B-041 | todo | spec: backlog row B-041 (`git show 13b3751:docs/planning/backlog.md`) |
| T-17 | Widget: daily forecast with warning inversion | 4 | T-08, T-14 | B-043 | todo | spec: backlog row B-043 (`git show 13b3751:docs/planning/backlog.md`) |
| T-18 | Widget: hourly table (Tavlan) | 4 | T-08, T-10, T-14 | B-042 | todo | spec: backlog row B-042 (`git show 13b3751:docs/planning/backlog.md`) |
| T-19 | Widget: stat / key-value | 3 | T-03 | B-051 | todo | spec: backlog row B-051 (`git show 13b3751:docs/planning/backlog.md`) |
| T-20 | Widget: room list | 2 | T-03 | B-048 | todo | spec: backlog row B-048 (`git show 13b3751:docs/planning/backlog.md`) |
| T-21 | Widget: energy flow | 5 | T-03, T-06 | B-047 | todo | spec: backlog row B-047 (`git show 13b3751:docs/planning/backlog.md`) |
| T-22 | Widget: sun and moon | 2 | T-03 | B-050 | todo | spec: backlog row B-050 (`git show 13b3751:docs/planning/backlog.md`) |
| T-23 | "Empty house" gate | 2 | T-04, T-15 | B-045 | todo | spec: backlog row B-045 (`git show 13b3751:docs/planning/backlog.md`) |
| T-24 | Layout 01 Tidslinjen with the owner's changes | 3 | T-05, T-06, T-15, T-16, T-17 | B-046 | todo | spec: backlog row B-046 (`git show 13b3751:docs/planning/backlog.md`) |
| T-25 | Panel profiles from the TRMNL model table | 4 | — | B-064 | todo | spec: backlog row B-064 (`git show 13b3751:docs/planning/backlog.md`) |
| T-26 | 2-bit and 4-bit render paths | 4 | T-25 | B-065 | todo | spec: backlog row B-065 (`git show 13b3751:docs/planning/backlog.md`) |

## Scope changes

## Retro
