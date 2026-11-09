# Roadmap — paperboard

## Current position
**Active sprint:** 05 (opened 2026-11-09).
**Current ticket:** Sprint 05 T-01.
**Last completed:** Sprint 04 T-11 (commit `6fffaba`).

## Sprints
| Sprint | Goal | Status |
|---|---|---|
| 01 | Skeleton and device server: the stack proven (phase 0), and HA serving a TRMNL-compatible image with telemetry to the emulated client (phase 1 code) | done |
| 02 | Layout engine and the hard widgets: mockup 01 from YAML on real data, empty-house gate, 2-bit | done |
| 03 | All designs as layouts, schedule, release readiness (phases 3–5 minus owner decisions) | done |
| 04 | Internationalisation for 0.2.0: English default, optional Swedish, contributable languages | done |
| 05 | English polish for 0.2.0: no cut-off labels, no flaky test | active |

## Go/no-go (Sprint 01 T-13, 2026-11-08)
**GO.** Mockup 01 with the owner's changes was hand-built from the 2026-11-08 fixture and
rendered by the pipeline: a 1-bit PNG of ~6.3 kB, 0 % grey, crisp TRMNL pixel fonts, and
price and solar on one shared time axis
(`tests/golden/proto_tidslinjen.png`). The solar curve in the prototype is an approximation
(see B-081).

