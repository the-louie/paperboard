# Sprint 04 — Internationalisation (0.2.0)
**Status:** active (opened 2026-11-09)
**Current ticket:** T-11
**Last completed:** T-10
**Budget:** 31h estimated (band 80–120h). **Below the band on purpose:** the owner scoped this
loop to the 0.2.0 internationalisation rows only (B-105 to B-115); B-116 is the owner's release.

## Goal
English is the default for every drawn text, Swedish is optional, and a contributor adds a
language with two JSON files. Plan and test plan: `docs/design/i18n.md`.

## Demo
- Every bundled layout rendered in English on the owner's fixture with no Swedish word, and in
  Swedish pixel-identical to the 0.1.x goldens (except the `Uterum` label fix).
- A throwaway HA 2026.11.0 rendering English, then Swedish after a language switch, then
  English for `de`.

## Tickets
| ID | Title | Est h | Deps | From | Status | Notes |
|---|---|---|---|---|---|---|
| T-01 | i18n core: catalogs, resolution, lookup | 3 | — | B-105 | done | i18n.py, layout pin any code, default en; test snapshots pinned sv |
| T-02 | Move date and agenda vocabulary | 4 | T-01 | B-106 | done | catalogs generated from the old tables; sv goldens identical |
| T-03 | Move weather conditions and prose | 4 | T-01 | B-107 | done | and/och grammar is a template; sv goldens identical |
| T-04 | Move labels (now block, energy, flow, charts, sky, footer) | 4 | T-01 | B-108 | done | no lang branches left in widgets; sv "indoor" = Inne; sv goldens identical (fixture names the room) |
| T-05 | Layout texts: section keys and layout display names | 3 | T-01 | B-109 | done | `{key: …}` titles; dropdown "Timeline (bundled)"; ids unchanged |
| T-06 | Numbers follow the language | 2 | T-01 | B-110 | done | fmt default en; now_block passed no lang (4 calls) |
| T-07 | Test suite for i18n | 5 | T-02..T-06 | B-111 | done | stray-word tests both ways (mutation-checked), 7 `*_owner_en` goldens, empty in every language, renderer follows HA |
| T-08 | HA UI texts audit | 1 | — | B-112 | done | already British and complete; spelling guard test added |
| T-09 | Docs: add-a-language guide, README language section | 2 | T-01, T-05 | B-113 | done | e4a02f1 |
| T-10 | README images from the English default | 1 | T-07 | B-114 | done | images = English goldens, guarded by a test; --lang for translators |
| T-11 | End-to-end language check in a throwaway HA | 2 | T-07 | B-115 | todo | |

## Scope changes
- Found: an intermittent ERROR in the suite, filed as **B-117** (not in this sprint).
- Found: English labels cut off in narrow cells, filed as **B-118** (P1, next sprint).

## Retro
