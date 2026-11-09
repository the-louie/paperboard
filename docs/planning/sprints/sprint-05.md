# Sprint 05 — English polish for 0.2.0
**Status:** done (closed 2026-11-09)
**Current ticket:** —
**Last completed:** T-02
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
| T-02 | Flaky: an intermittent ERROR in the full suite | 1 | — | B-117 | done | not reproduced: 16 full runs clean (4 with cleared bytecode caches); both sightings were the first run after an edit. Reopen with the -rE output if it returns |

## Scope changes

## Retro
**Shipped (2/2):** no English label is cut off on the bundled layouts (short forms only where
the full label does not fit; regression test); the flaky error did not reproduce in 16 runs.
**For the owner:** Swedish Almanac still cuts "KÄNNS S…" and "IMORGO…" (as in 0.1.x); a
Swedish short form is the owner's wording to choose. Long data lines (the footer's room list,
the weather summary, the TRMNL title bar's date line) are cut in both languages, as before.
