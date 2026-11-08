# Roadmap — paperboard

## Current position
**Active sprint:** [Sprint 02](./sprints/sprint-02.md) — in progress.
**Current ticket:** Sprint 02 T-12 (`todo` — Solar forecast adapter).
**Last completed:** Sprint 02 T-11 (commit `7764679`).

## Sprints
| Sprint | Goal | Status |
|---|---|---|
| 01 | Skeleton and device server: the stack proven (phase 0), and HA serving a TRMNL-compatible image with telemetry to the emulated client (phase 1 code) | done |
| 02 | Layout engine and the hard widgets: mockup 01 from YAML on real data, empty-house gate, 2-bit | in progress |
| 03 | All 8 designs as layouts, time-of-day schedule, calendar and text slots (phase 3) | goal only |

## Go/no-go (Sprint 01 T-13, 2026-11-08)
**GO.** Mockup 01 with the owner's changes was hand-built from the 2026-11-08 fixture and
rendered by the pipeline: a 1-bit PNG of ~6.3 kB, 0 % grey, crisp TRMNL pixel fonts, and
price and solar on one shared time axis
(`tests/golden/proto_tidslinjen.png`). The solar curve in the prototype is an approximation
(see B-081).

