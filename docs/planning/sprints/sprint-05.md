# Sprint 05 — English polish for 0.2.0
**Status:** active (opened 2026-11-09)
**Current ticket:** T-02
**Last completed:** T-01
**Budget:** 3h estimated. Below the band on purpose: the work Sprint 04 found inside the
owner's internationalisation scope; B-116 (release) is the owner's.

## Goal
No English label is cut off on the bundled layouts, and the suite has no intermittent error.

## Demo
- The `*_owner_en` goldens show "Tomorrow", "Rain today" and "Solar expected today" in full
  (or a deliberate short form), with the Swedish goldens unchanged.
- 10 full-suite runs in a row without an ERROR.

## Tickets
| ID | Title | Est h | Deps | From | Status | Notes |
|---|---|---|---|---|---|---|
| T-01 | English labels cut off in narrow cells | 2 | — | B-118 | done | short forms only when the full label does not fit (energy) and grid labels ("Tmrw 07", "Rain"); sv bento "Sol idag"; regression test |
| T-02 | Flaky: an intermittent ERROR in the full suite | 1 | — | B-117 | todo | |

## Scope changes

## Retro
