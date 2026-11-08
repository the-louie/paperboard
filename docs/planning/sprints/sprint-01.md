# Sprint 01 — Skeleton and device server: the stack proven, HA serves a TRMNL image
**Status:** in progress (opened 2026-11-08)
**Current ticket:** T-29 (`todo` — Performance budget)
**Last completed:** T-28 (`done` — commit `f5fd2d4`)
**Budget:** 81h estimated (band 80–120h)

## Goal
Prove the resvg + Pillow stack and build the integration skeleton, so that a paperboard hub with one screen answers the TRMNL device API and serves a 1-bit PNG.

## Demo
- The emulated TRMNL client (`scripts/fake_trmnl.py`) pairs against paperboard running in the test harness (setup → display → image → log).
- It receives a 1-bit PNG under 90 kB showing the "now" block and footer. Telemetry sensors show its battery and RSSI.
- The static mockup 01 render is shown next to the HTML mockup, with the go/no-go recorded.

## Tickets
| ID | Title | Est h | Deps | From | Status | Notes |
|---|---|---|---|---|---|---|
| T-01 | Repo scaffold | 3 | — | B-001 | done | Landed in 052e587 |
| T-02 | Research: HA test harness on Python 3.14 | 2 | T-01 | B-002 | done | Landed in 64e61b8 |
| T-03 | Research: route collision and auth under /api | 2 | — | B-003 | done | Landed in f625b35 |
| T-04 | Research: the owner's TRMNL OG facts | 1 | — | B-004 | done | Landed in f5c7d66 |
| T-05 | Spike: resvg-py in an HA 2026.11 throwaway container | 3 | T-01 | B-005 | done | Landed in 21df590 |
| T-06 | Fonts: bundle and load | 2 | T-01 | B-007 | done | Landed in da23d2e |
| T-07 | Spike: text metrics, Pillow vs resvg | 3 | T-06 | B-006 | done | Landed in 25119f4 |
| T-08 | Text measurement and wrap utility | 3 | T-07 | B-080 | done | Landed in 65929c1 |
| T-09 | Unit-format helpers | 2 | T-01 | B-079 | done | Landed in a2e9296 |
| T-10 | Pipeline: SVG → panel PNG | 4 | T-05, T-06 | B-008 | done | Landed in 5098412 |
| T-11 | Golden-image test harness | 3 | T-10 | B-009 | done | Landed in 6bbee34 |
| T-12 | Fixture capture script | 2 | T-11 | B-076 | done | Landed in 2158d1e |
| T-13 | Static render of mockup 01 (go/no-go) | 4 | T-10, T-11, T-08, T-09 | B-010 | done | Landed in 4fc2201 |
| T-14 | Research: pairing semantics | 2 | T-03 | B-011 | done | Landed in 20019e2 |
| T-15 | Config flow: hub entry | 3 | T-02 | B-012 | done | Landed in fcc0162 |
| T-16 | Config subentry: Screen | 4 | T-15 | B-013 | done | Landed in 1cab556 |
| T-17 | Emulated TRMNL client | 3 | T-01 | B-016 | done | Landed in feaffea |
| T-18 | Image view plus last-good cache | 3 | T-10, T-02 | B-018 | done | Landed in 7b25cc3 |
| T-19 | View: /api/setup with a pairing window | 4 | T-14, T-16, T-17 | B-014 | done | Landed in e5f798b |
| T-20 | View: /api/display | 4 | T-19, T-18 | B-015 | done | Landed in 1e4621c |
| T-21 | View: /api/log | 2 | T-20 | B-017 | done | Landed in ad83f21 |
| T-22 | ImageEntity per screen | 2 | T-18, T-16 | B-019 | done | Landed in cde6d5e |
| T-23 | Render scheduler | 5 | T-10, T-16 | B-020 | done | Landed in 9a5f85b |
| T-24 | Telemetry sensors | 3 | T-20 | B-021 | done | Landed in 4c7780c |
| T-25 | Missed-check-in problem sensor | 2 | T-24 | B-022 | done | Landed in ac4b6a4 |
| T-26 | Widgets: "now" block and status footer | 4 | T-13 | B-023 | done | Landed in 9abd698 |
| T-27 | Diagnostics and redaction | 2 | T-19 | B-024 | done | Landed in 04d2e22 |
| T-28 | Security review of the device endpoints | 2 | T-20, T-18 | B-073 | done | Landed in f5fd2d4 |
| T-29 | Performance budget | 2 | T-23, T-26 | B-074 | todo | spec: backlog row B-074 (git show 13b3751:docs/planning/backlog.md) |

## Scope changes

## Retro
