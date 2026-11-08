# Sprint 03 — All designs, the schedule, and release readiness
**Status:** in progress (opened 2026-11-08)
**Current ticket:** T-13 (`todo` — Layout 08 Energi)
**Last completed:** T-12 (`done` — commit `50146dc`)
**Budget:** 59h estimated (band 80–120h). **Below the band on purpose: this is all the
schedulable work left.** The remaining rows are owner decisions (deploy, device switch,
schedule choice, decommission, release) and two rows that depend on them.

## Goal
Every approved design as a YAML layout with the owner's changes, a time-of-day schedule with
night sleep, and the repo ready for a public HACS release (docs, CI, brand, aarch64 checked).

## Demo
- Goldens of 02 Tidningen, 03 Bento, 05 Tavlan, 06 TRMNL, 07 Almanackan and 08 Energi on the
  owner's data, plus 01 from Sprint 02. All 1-bit, all under 90 kB, all passing the
  empty-house gate.
- A schedule test switching Tavlan in for 07–08 on school days.
- README with the widget catalogue; CI workflow green locally (ruff, pytest).

## Tickets
| ID | Title | Est h | Deps | From | Status | Notes |
|---|---|---|---|---|---|---|
| T-01 | Widget: calendar agenda | 4 | — | B-049 | done | Landed in 414ce0f |
| T-02 | Widget: headline/prose text slot | 3 | — | B-052 | done | Landed in 474eb77 |
| T-03 | Area frames: rounded boxes and an inverted hero | 3 | — | B-084 | done | Landed in 38358a4 |
| T-04 | Header variants: masthead and title bar | 2 | — | B-085 | done | Landed in 73ee31f |
| T-05 | Inverted now panel (Tavlan) | 2 | T-03 | B-086 | done | Landed in d6c6566 |
| T-06 | Schedule: time-of-day layouts | 4 | — | B-060 | done | Landed in 5990438 |
| T-07 | Night sleep and refresh policy | 2 | T-06 | B-061 | done | Landed in d04f65b |
| T-08 | Layout 02 Tidningen | 2 | T-02, T-04 | B-053 | done | Landed in 6e69fe3 |
| T-09 | Layout 03 Bento | 2 | T-03 | B-054 | done | Landed in e97f48c |
| T-10 | Layout 05 Tavlan | 2 | T-05 | B-055 | done | Landed in 2ecfa56 |
| T-11 | Layout 06 TRMNL | 2 | T-03, T-04 | B-056 | done | Landed in 0faf462 |
| T-12 | Layout 07 Almanackan | 2 | T-01 | B-057 | done | Landed in 50146dc |
| T-13 | Layout 08 Energi | 2 | — | B-058 | todo | spec: backlog row B-058 |
| T-14 | Layout 04 Instrument (bar-chart parts only) | 1 | — | B-059 | todo | spec: backlog row B-059 |
| T-15 | Scale YAML layouts to larger panels | 4 | — | B-083 | todo | spec: backlog row B-083 |
| T-16 | Localisation of widget texts | 3 | — | B-075 | todo | spec: backlog row B-075 |
| T-17 | Rotate-image-token button per screen | 2 | — | B-082 | todo | spec: backlog row B-082 |
| T-18 | Generic image clients | 3 | — | B-066 | todo | spec: backlog row B-066 |
| T-19 | Spike: a Lovelace preview card (optional) | 3 | — | B-078 | todo | spec: backlog row B-078 |
| T-20 | Research: aarch64 verification | 2 | — | B-070 | todo | spec: backlog row B-070 |
| T-21 | CI workflow | 3 | — | B-069 | todo | spec: backlog row B-069 |
| T-22 | Brand assets | 1 | — | B-068 | todo | spec: backlog row B-068 |
| T-23 | README and documentation | 5 | T-08, T-09, T-10, T-11, T-12, T-13, T-06 | B-067 | todo | spec: backlog row B-067 |

## Scope changes

## Retro
