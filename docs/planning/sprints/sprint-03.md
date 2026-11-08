# Sprint 03 — All designs, the schedule, and release readiness
**Status:** done (closed 2026-11-08)
**Current ticket:** —
**Last completed:** T-23 (`done` — commit `233fed1`)
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
| T-13 | Layout 08 Energi | 2 | — | B-058 | done | Landed in 159b76e |
| T-14 | Layout 04 Instrument (bar-chart parts only) | 1 | — | B-059 | done | Landed in 6bb7858 |
| T-15 | Scale YAML layouts to larger panels | 4 | — | B-083 | done | Landed in 0526c30 |
| T-16 | Localisation of widget texts | 3 | — | B-075 | done | Landed in e6e3e35 |
| T-17 | Rotate-image-token button per screen | 2 | — | B-082 | done | Landed in fcb6873 |
| T-18 | Generic image clients | 3 | — | B-066 | done | Landed in da20435 |
| T-19 | Spike: a Lovelace preview card (optional) | 3 | — | B-078 | done | Landed in 7226cd6 |
| T-20 | Research: aarch64 verification | 2 | — | B-070 | done | Landed in 34f0de9 |
| T-21 | CI workflow | 3 | — | B-069 | done | Landed in ce23593 |
| T-22 | Brand assets | 1 | — | B-068 | done | Landed in e39187c |
| T-23 | README and documentation | 5 | T-08, T-09, T-10, T-11, T-12, T-13, T-06 | B-067 | done | Landed in 233fed1 |

## Scope changes
- **T-15** closed its grid/type half; widget-internal offset scaling was returned as **B-087** (P3).
- **New widget types inside layout tickets** (each needed by its design): `hourly_strip` and `tomorrow` (T-09); `date`, `week` and `now_grid` (T-12); flag role `grid_export_positive` (T-13); `grid.paddings` (T-11).

## Retro
**Shipped (23/23 tickets, 232 tests, ruff clean):**
- **Six more designs as YAML layouts on the owner's data** (Tidningen, Bento, Tavlan, TRMNL,
  Almanackan, Energi), each with the owner's changes. With Sprint 02's Tidslinjen that is all
  seven approved designs; 04 was rejected except its bar style, which lives on in the price
  chart.
- **Layout system:** calendar agenda and events, text slots (HA templates, automatic headline),
  frames/gaps/margins, header variants, the black panel, time-of-day schedules with
  wake-after-switch.
- **Product:** refresh policy, scaling to big panels, localisation tables, rotate-image-link
  button.
- **Release prep:** generic-client docs, aarch64 static check, CI workflow (x86 + ARM, hassfest,
  HACS), brand assets, README.

**Bugs found by tests:** a hub reload within 1 s of pairing lost the device key (fixed with a
flush on unload, T-17). The header ran into the tomorrow badge in narrow columns (fixed, T-10).

**Not shipped:** nothing. B-087 (widget offsets on big panels) is returned to the backlog.

**Estimate accuracy:** 59 h estimated for 23 tickets. The layout tickets (2 h each) ran over
because each needed new widgets (~+6 h total). The doc and research tickets ran under.

**What is left (backlog):**
- B-087, P3, schedulable: widget offsets on big panels; the owner has no big panel.
- Owner decisions:
  - B-025: deploy to production HA;
  - B-026: point the device at HA;
  - B-062: pick the schedule;
  - B-063: decommission byos-host's byos;
  - B-071: release and the HACS PR;
  - B-081: relink the solar forecast.
- Rows blocked by those decisions:
  - B-077: watchdog alert, needs the deploy;
  - B-072: upstream offer, needs the release.

