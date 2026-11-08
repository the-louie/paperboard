# Roadmap — paperboard

## Current position
**Active sprint:** [Sprint 03](./sprints/sprint-03.md) — in progress.
**Current ticket:** Sprint 03 T-02 (`todo` — Widget: headline/prose text slot).
**Last completed:** Sprint 03 T-01 (commit `414ce0f`).

## Sprints
| Sprint | Goal | Status |
|---|---|---|
| 01 | Skeleton and device server: the stack proven (phase 0), and HA serving a TRMNL-compatible image with telemetry to the emulated client (phase 1 code) | done |
| 02 | Layout engine and the hard widgets: mockup 01 from YAML on real data, empty-house gate, 2-bit | done |
| 03 | All designs as layouts, schedule, release readiness (phases 3–5 minus owner decisions) | in progress |

## Go/no-go (Sprint 01 T-13, 2026-11-08)
**GO.** Mockup 01 with the owner's changes was hand-built from the 2026-11-08 fixture and
rendered by the pipeline: a 1-bit PNG of ~6.3 kB, 0 % grey, crisp TRMNL pixel fonts, and
price and solar on one shared time axis
(`tests/golden/proto_tidslinjen.png`). The solar curve in the prototype is an approximation
(see B-081).

