# Backlog — paperboard

Next ID: **B-119**

**Sources:**
      Measured 18:05 on ha-host: a **warm** render takes **1,149 ms** (the max was 3,674 ms
      just after a restart), against ~80 ms on dev-host. That matters more now: a button
      press waits for one render before the panel gets its answer (B-089).
- R = `docs/research/HACS e-ink dashboard renderer.md` (deep research 2026-11-08), § = section.
- N = research notes in `<the maintainer's HA repo> e-ink dashboard renderer/`.
- V = vault page `servers/trmnl-dashboard/trmnl-dashboard.md` (owner feedback per mockup, design rules).
- M = mockup HTML `<the maintainer's notes>`.

## Last grooming 2026-11-08

This is the first refinement pass of the 6-phase plan (R §phases).

- **Order:** research tickets that de-risk a later choice come before the code that depends on
  them.
- **Splits:** every row is 1–6 h.
- **`decision:` rows:** physical-device switches and production deploys belong to the owner.
- **Goal of each phase:**
  - Phase 0: prove the stack.
  - Phase 1: the OG is served from HA.
  - Phase 2: the main mockup runs on real data.
  - Phase 3: all 8 mockups plus a schedule.
  - Phase 4: other panels.
  - Phase 5: public HACS release.

---

## Phase 0 — Spike: prove the rendering stack (goal: one mockup rendered in-process, ready for go/no-go)

- ~~**B-001 · Repo scaffold**~~ — CLOSED 2026-11-08 (Sprint 01 T-01): see commit "T-01: Repo scaffold"
- ~~**B-002 · Research: HA test harness on Python 3.14**~~ — CLOSED 2026-11-08 (Sprint 01 T-02): see commit "T-02: Research: HA test harness on Python 3.14"
- ~~**B-003 · Research: route collision and auth under /api**~~ — CLOSED 2026-11-08 (Sprint 01 T-03): see commit "T-03: Research: route collision and auth under /api"
- ~~**B-004 · Research: the owner's TRMNL OG facts**~~ — CLOSED 2026-11-08 (Sprint 01 T-04): see commit "T-04: Research: the owner's TRMNL OG facts"
- ~~**B-005 · Spike: resvg-py in an HA 2026.11 throwaway container**~~ — CLOSED 2026-11-08 (Sprint 01 T-05): see commit "T-05: Spike: resvg-py in an HA 2026.11 throwaway container"
- ~~**B-006 · Spike: text metrics, Pillow vs resvg**~~ — CLOSED 2026-11-08 (Sprint 01 T-07): see commit "T-07: Spike: text metrics, Pillow vs resvg"
- ~~**B-007 · Fonts: bundle and load**~~ — CLOSED 2026-11-08 (Sprint 01 T-06): see commit "T-06: Fonts: bundle and load"
- ~~**B-008 · Pipeline: SVG → panel PNG**~~ — CLOSED 2026-11-08 (Sprint 01 T-10): see commit "T-10: Pipeline: SVG → panel PNG"
- ~~**B-009 · Golden-image test harness**~~ — CLOSED 2026-11-08 (Sprint 01 T-11): see commit "T-11: Golden-image test harness"
- ~~**B-010 · Static render of mockup 01 (go/no-go)**~~ — CLOSED 2026-11-08 (Sprint 01 T-13): see commit "T-13: Static render of mockup 01 (go/no-go)"

## Phase 1 — Device server (goal: the owner's OG is served from HA, battery and liveness monitored)

- ~~**B-011 · Research: pairing semantics**~~ — CLOSED 2026-11-08 (Sprint 01 T-14): see commit "T-14: Research: pairing semantics"
- ~~**B-012 · Config flow: hub entry**~~ — CLOSED 2026-11-08 (Sprint 01 T-15): see commit "T-15: Config flow: hub entry"
- ~~**B-013 · Config subentry: Screen**~~ — CLOSED 2026-11-08 (Sprint 01 T-16): see commit "T-16: Config subentry: Screen"
- ~~**B-014 · View: /api/setup with a pairing window**~~ — CLOSED 2026-11-08 (Sprint 01 T-19): see commit "T-19: View: /api/setup with a pairing window"
- ~~**B-015 · View: /api/display**~~ — CLOSED 2026-11-08 (Sprint 01 T-20): see commit "T-20: View: /api/display"
- ~~**B-016 · Emulated TRMNL client**~~ — CLOSED 2026-11-08 (Sprint 01 T-17): see commit "T-17: Emulated TRMNL client"
- ~~**B-017 · View: /api/log**~~ — CLOSED 2026-11-08 (Sprint 01 T-21): see commit "T-21: View: /api/log"
- ~~**B-018 · Image view plus last-good cache**~~ — CLOSED 2026-11-08 (Sprint 01 T-18): see commit "T-18: Image view plus last-good cache"
- ~~**B-019 · ImageEntity per screen**~~ — CLOSED 2026-11-08 (Sprint 01 T-22): see commit "T-22: ImageEntity per screen"
- ~~**B-020 · Render scheduler**~~ — CLOSED 2026-11-08 (Sprint 01 T-23): see commit "T-23: Render scheduler"
- ~~**B-021 · Telemetry sensors**~~ — CLOSED 2026-11-08 (Sprint 01 T-24): see commit "T-24: Telemetry sensors"
- ~~**B-022 · Missed-check-in problem sensor**~~ — CLOSED 2026-11-08 (Sprint 01 T-25): see commit "T-25: Missed-check-in problem sensor"
- ~~**B-023 · Widgets: "now" block and status footer**~~ — CLOSED 2026-11-08 (Sprint 01 T-26): see commit "T-26: Widgets: "now" block and status footer"
- ~~**B-024 · Diagnostics and redaction**~~ — CLOSED 2026-11-08 (Sprint 01 T-27): see commit "T-27: Diagnostics and redaction"
- ~~**B-025 · decision: deploy to production HA (ha-host)**~~ — CLOSED 2026-11-08: owner said "deploy paperboard". Copied to ha-host, HA restarted (146 s and 153 s), hub entry `01M6XZTM…`, roles bound, screen "Hallen" on schedule `/config/paperboard/hallen.yaml`. The live render found 3 bugs, fixed in 84d907f and e3c630c.
- ~~**B-026 · decision: owner points the OG at HA**~~ — CLOSED 2026-11-08: paired 17:51 CET after a second pairing window. The first window closed before the panel rebooted. First check-in: battery 4.20 V, RSSI −58 dBm, fw 1.8.10. byos-host byos was last called 17:34.
- ~~**B-027 · Research: schema library for layouts**~~ — CLOSED 2026-11-08 (Sprint 02 T-01): see commit "T-01: Research: schema library for layouts"
- ~~**B-028 · Design: layout YAML schema**~~ — CLOSED 2026-11-08 (Sprint 02 T-02): see commit "T-02: Design: layout YAML schema"
- ~~**B-029 · Layout loader and validation**~~ — CLOSED 2026-11-08 (Sprint 02 T-05): see commit "T-05: Layout loader and validation"
- ~~**B-030 · Grid engine with reflow**~~ — CLOSED 2026-11-08 (Sprint 02 T-04): see commit "T-04: Grid engine with reflow"
- ~~**B-031 · Type scale and style tokens**~~ — CLOSED 2026-11-08 (Sprint 02 T-03): see commit "T-03: Type scale and style tokens"
- ~~**B-032 · Roles: binding in config/options flow**~~ — CLOSED 2026-11-08 (Sprint 02 T-06): see commit "T-06: Roles: binding in config/options flow"
- ~~**B-033 · Repairs for missing entities**~~ — CLOSED 2026-11-08 (Sprint 02 T-07): see commit "T-07: Repairs for missing entities"
- ~~**B-034 · Data: weather forecasts**~~ — CLOSED 2026-11-08 (Sprint 02 T-08): see commit "T-08: Data: weather forecasts"
- ~~**B-035 · Research: price sources**~~ — CLOSED 2026-11-08 (Sprint 02 T-09): see commit "T-09: Research: price sources"
- ~~**B-036 · Price adapters**~~ — CLOSED 2026-11-08 (Sprint 02 T-10): see commit "T-10: Price adapters"
- ~~**B-037 · Research: solar forecast source**~~ — CLOSED 2026-11-08 (Sprint 02 T-11): see commit "T-11: Research: solar forecast source"
- ~~**B-038 · Solar forecast adapter**~~ — CLOSED 2026-11-08 (Sprint 02 T-12): see commit "T-12: Solar forecast adapter"
- ~~**B-039 · TimeAxis object**~~ — CLOSED 2026-11-08 (Sprint 02 T-13): see commit "T-13: TimeAxis object"
- ~~**B-040 · Widget: price chart**~~ — CLOSED 2026-11-08 (Sprint 02 T-15): see commit "T-15: Widget: price chart"
- ~~**B-041 · Widget: solar forecast chart**~~ — CLOSED 2026-11-08 (Sprint 02 T-16): see commit "T-16: Widget: solar forecast chart"
- ~~**B-042 · Widget: hourly table (Tavlan)**~~ — CLOSED 2026-11-08 (Sprint 02 T-18): see commit "T-18: Widget: hourly table (Tavlan)"
- ~~**B-043 · Widget: daily forecast with warning inversion**~~ — CLOSED 2026-11-08 (Sprint 02 T-17): see commit "T-17: Widget: daily forecast with warning inversion"
- ~~**B-044 · Weather icon set**~~ — CLOSED 2026-11-08 (Sprint 02 T-14): see commit "T-14: Weather icon set"
- ~~**B-045 · "Empty house" gate**~~ — CLOSED 2026-11-08 (Sprint 02 T-23): see commit "T-23: "Empty house" gate"
- ~~**B-046 · Layout 01 Tidslinjen with the owner's changes**~~ — CLOSED 2026-11-08 (Sprint 02 T-24): see commit "T-24: Layout 01 Tidslinjen with the owner's changes"

## Phase 3 — Remaining widgets and the schedule (goal: all 8 mockups in rotation, night sleep)

- ~~**B-047 · Widget: energy flow**~~ — CLOSED 2026-11-08 (Sprint 02 T-21): see commit "T-21: Widget: energy flow"
- ~~**B-048 · Widget: room list**~~ — CLOSED 2026-11-08 (Sprint 02 T-20): see commit "T-20: Widget: room list"
- ~~**B-049 · Widget: calendar agenda**~~ — CLOSED 2026-11-08 (Sprint 03 T-01): see commit "T-01: Widget: calendar agenda"
- ~~**B-050 · Widget: sun and moon**~~ — CLOSED 2026-11-08 (Sprint 02 T-22): see commit "T-22: Widget: sun and moon"
- ~~**B-051 · Widget: stat / key-value**~~ — CLOSED 2026-11-08 (Sprint 02 T-19): see commit "T-19: Widget: stat / key-value"
- ~~**B-052 · Widget: headline/prose text slot**~~ — CLOSED 2026-11-08 (Sprint 03 T-02): see commit "T-02: Widget: headline/prose text slot"
- ~~**B-053 · Layout 02 Tidningen**~~ — CLOSED 2026-11-08 (Sprint 03 T-08): see commit "T-08: Layout 02 Tidningen"
- ~~**B-054 · Layout 03 Bento**~~ — CLOSED 2026-11-08 (Sprint 03 T-09): see commit "T-09: Layout 03 Bento"
- ~~**B-055 · Layout 05 Tavlan**~~ — CLOSED 2026-11-08 (Sprint 03 T-10): see commit "T-10: Layout 05 Tavlan"
- ~~**B-056 · Layout 06 TRMNL**~~ — CLOSED 2026-11-08 (Sprint 03 T-11): see commit "T-11: Layout 06 TRMNL"
- ~~**B-057 · Layout 07 Almanackan**~~ — CLOSED 2026-11-08 (Sprint 03 T-12): see commit "T-12: Layout 07 Almanackan"
- ~~**B-058 · Layout 08 Energi**~~ — CLOSED 2026-11-08 (Sprint 03 T-13): see commit "T-13: Layout 08 Energi"
- ~~**B-059 · Layout 04 Instrument (bar-chart parts only)**~~ — CLOSED 2026-11-08 (Sprint 03 T-14): see commit "T-14: Layout 04 Instrument (bar-chart parts only)"
- ~~**B-060 · Schedule: time-of-day layouts**~~ — CLOSED 2026-11-08 (Sprint 03 T-06): see commit "T-06: Schedule: time-of-day layouts"
- ~~**B-061 · Night sleep and refresh policy**~~ — CLOSED 2026-11-08 (Sprint 03 T-07): see commit "T-07: Night sleep and refresh policy"
- ~~**B-062 · decision: which layout when**~~ — CLOSED 2026-11-08: owner accepted: Tavlan 06:30–08:00 on weekdays, Tidslinjen otherwise, 23:00–06:00 waking hourly (`hallen.yaml` on ha-host).
- [x] **B-063 · decision: decommission byos-host trmnl-byos and the screenshot cron** · done 2026-11-09 (owner): container removed, cron removed, HA dashboard and helper sensors removed · 1h · prio P3 · needs: B-026, B-062 · src: V phase 3
      After one stable week. Claude prepares the steps, and the owner OKs them.

## Phase 4 — Other panels (goal: a second panel type from the same layouts)

- ~~**B-064 · Panel profiles from the TRMNL model table**~~ — CLOSED 2026-11-08 (Sprint 02 T-25): see commit "T-25: Panel profiles from the TRMNL model table"
- ~~**B-065 · 2-bit and 4-bit render paths**~~ — CLOSED 2026-11-08 (Sprint 02 T-26): see commit "T-26: 2-bit and 4-bit render paths"
- ~~**B-066 · Generic image clients**~~ — CLOSED 2026-11-08 (Sprint 03 T-18): see commit "T-18: Generic image clients"

## Phase 5 — Publish (goal: a public HACS install another home can configure with no code)

- ~~**B-067 · README and documentation**~~ — CLOSED 2026-11-08 (Sprint 03 T-23): see commit "T-23: README and documentation"
- ~~**B-068 · Brand assets**~~ — CLOSED 2026-11-08 (Sprint 03 T-22): see commit "T-22: Brand assets"
- ~~**B-069 · CI workflow**~~ — CLOSED 2026-11-08 (Sprint 03 T-21): see commit "T-21: CI workflow"
- ~~**B-070 · Research: aarch64 verification**~~ — CLOSED 2026-11-08 (Sprint 03 T-20): see commit "T-20: Research: aarch64 verification"
- [x] **B-071 · decision: release and HACS default PR** · done 2026-11-09: v0.1.0 released, hacs/default PR #13762 ready for review · 1h · prio P3 · needs: B-067, B-069, B-070 · src: N HACS rules
      The owner pushes, tags the release, and opens a PR to hacs/default.
- [x] **B-101 · HACS review: token out of entity state, no re-pair without the window** · 2h · prio P0 · src: hacs/default #13762 review (frenck) 2026-11-09 · done 2026-11-09
      Review: (1) `png_path`/`bmp_path` attributes put the image token where every user and
      the recorder see it; (2) a known MAC re-paired outside the window, and any LAN device
      sees MACs. Owner 2026-11-09: "yes fix both first, then we'll do our own security qa".
      Fix: attributes removed, links shown in the screen's Reconfigure dialog (admin-only);
      `/api/setup` needs the window for every MAC. This reverses B-094. Changelog tells 0.1.0
      users to rotate the image link. Tests: test_generic_clients.py (token not in any state),
      test_setup_view.py (spoofed known MAC refused, real key kept), test_subentry_flow.py.
      Next: the owner's own security QA, then release 0.1.1 and re-request review.
- [x] **B-102 · Own security QA after the HACS review** · 6h · prio P1 · src: owner 2026-11-09 · done 2026-11-09
      Owner: "add 1, 2, 3, 5 with the re-pair notice, 6 and 7. issue 8 will be fixed after
      release. do the fixes as one commit each." Done: proxy-forwarded client addresses must
      be local to pair; diagnostics scrub tokens, keys, MACs, base URL and rejected IP; every
      pairing raises a notification; Repairs issues for a known panel asking to re-pair (with
      the asking and last check-in addresses) and for >10 bad-key polls an hour; /api/log
      limit on bytes read and 500-character fields; ID header capped at 64 characters.
      Withdrawn: Repairs prompt to rotate 0.1.0 tokens (no 0.1.0 users besides the lab).
- [x] **B-103 · CI: `permissions: contents: read` in every workflow** · 0.5h · prio P3 · src: B-102 · done 2026-11-09 (owner: "do the ci fix also before release")
      Keep `hacs/action@main` and `hassfest@master`; optionally pin the other actions by SHA
      with Dependabot for github-actions.
- [x] **B-104 · README: install from the HACS catalog first** · 0.5h · prio P2 · src: hacs/default #13762 approval (frenck) 2026-11-09 · done 2026-11-09, released in 0.1.2
      Paperboard was merged into the HACS default list 2026-11-09 21:02 (v0.1.1). Reviewer:
      "lead with searching for Paperboard in HACS and keep the custom repository route as a
      fallback". For the next release.
- [ ] **B-072 · Upstream offer to cryptomilk** · 1h · prio P3 · needs: B-071 · src: R §build new
      Claude drafts an issue offering the device-API views; the owner posts it.

## 0.2.0 — Internationalisation (goal: English default, optional Swedish, contributable languages)

Plan and test plan: `docs/design/i18n.md`. Owner 2026-11-09: "we ship with english default and
optional swedish", "we need this in next version, it can be 0.2.0".

- ~~**B-105 · i18n core: catalogs, resolution, lookup**~~ — CLOSED 2026-11-09 (Sprint 04 T-01 317952a)
      `i18n/en.json` + `sv.json`, `i18n.py` (`load_catalogs` in the executor, `resolve`, `t`,
      `tl`), `Snapshot.lang` default `en`, renderer and layout `lang:` pin use `resolve`.
      Accept: tests 2, 3, 8, 11.
- ~~**B-106 · Move date and agenda vocabulary**~~ — CLOSED 2026-11-09 (Sprint 04 T-02 d862d02)
      Weekday/month/short names, today/tomorrow, week, agenda words, holiday names; remove the 5
      duplicate tables. Accept: `*_owner` goldens identical; test 9.
- ~~**B-107 · Move weather conditions and prose**~~ — CLOSED 2026-11-09 (Sprint 04 T-03 972651d)
      `CONDITION`, `HEADLINE` and the and/och grammar as templates; "low", "dry". Accept:
      goldens identical.
- ~~**B-108 · Move labels (now block, energy, flow, charts, sky, footer)**~~ — CLOSED 2026-11-09 (Sprint 04 T-04 60100dc)
      Every remaining `lang == "sv"` branch and label table, including chart labels and the
      `Uterum` bug (sv "indoor" becomes "Inne"). Accept: no `== "sv"` left in widget code;
      goldens identical except the Uterum label.
- ~~**B-109 · Layout texts: section keys and layout display names**~~ — CLOSED 2026-11-09 (Sprint 04 T-05 b74a7a4)
      `title: {key: …}` in bundled layouts, `layout_text()` handles string/dict/key; layout
      dropdown shows `layout.<id>`; ids unchanged. Accept: subentry flow test shows "Timeline"
      in en.
- ~~**B-110 · Numbers follow the language**~~ — CLOSED 2026-11-09 (Sprint 04 T-06 18643a2)
      `fmt` default `en`; every caller passes `snap.lang`. Accept: test 10.
- ~~**B-111 · Test suite for i18n**~~ — CLOSED 2026-11-09 (Sprint 04 T-07 35cee33)
      Tests 1, 4, 5, 7, 12 and an `*_owner_en` golden per bundled layout; `*_owner` goldens
      pinned `lang="sv"`.
- ~~**B-112 · HA UI texts audit**~~ — CLOSED 2026-11-09 (Sprint 04 T-08 d77e938)
      `strings.json` English first and complete, sv complete, no Swedish in English strings.
- ~~**B-113 · Docs: add-a-language guide, README language section**~~ — CLOSED 2026-11-09 (Sprint 04 T-09 e4a02f1)
      CONTRIBUTING, README, layout-schema (keys), CHANGELOG.
- ~~**B-114 · README images from the English default**~~ — CLOSED 2026-11-09 (Sprint 04 T-10 e0883e7)
      `scripts/readme_images.py` renders with the default language; images regenerated.
- ~~**B-115 · End-to-end language check in a throwaway HA**~~ — CLOSED 2026-11-09 (Sprint 04 T-11 6fffaba)
      Test 13: en, sv, de on HA 2026.11.0 in a container; no errors.
- ~~**B-118 · English labels cut off in narrow cells**~~ — CLOSED 2026-11-09 (Sprint 05 T-01 48b6191)
      Almanac now-grid: "TOMORR…", "RAIN TO…"; Newspaper and Bento energy: "Solar expected
      to…". English is the default now, so the labels need short forms that fit (catalog keys
      for compact labels, e.g. `now_rows_short`), checked on the `*_owner_en` goldens.
- ~~**B-117 · Flaky: an intermittent ERROR in the full suite**~~ — CLOSED 2026-11-09 (Sprint 05 T-02, not reproduced in 16 runs)
      Once as `test_subentry_flow::test_layout_is_a_dropdown_with_bundled_and_own_files`
      (error, not failure: setup/teardown), once unnamed; reruns pass. Find the leaking timer
      or task.
- [x] **B-116 · decision: release 0.2.0** · owner 2026-11-09: "0.1.2 was never pushed, merge it into 0.2.0"; bumped and tagged locally, owner pushes · 1h · prio P1 · needs: B-115 · src: owner
      Version bump and tag by Claude; push, release and HACS check by the owner.

## Cross-cutting

- ~~**B-073 · Security review of the device endpoints**~~ — CLOSED 2026-11-08 (Sprint 01 T-28): see commit "T-28: Security review of the device endpoints"
- ~~**B-074 · Performance budget**~~ — CLOSED 2026-11-08 (Sprint 01 T-29): see commit "T-29: Performance budget"
- ~~**B-075 · Localisation of widget texts**~~ — CLOSED 2026-11-08 (Sprint 03 T-16): see commit "T-16: Localisation of widget texts"
- ~~**B-076 · Fixture capture script**~~ — CLOSED 2026-11-08 (Sprint 01 T-12): see commit "T-12: Fixture capture script"
- ~~**B-077 · Device liveness → owner alert**~~ — CLOSED 2026-11-08: the AppDaemon watchdog got an `expect_off` option. `binary_sensor.hallen_uteblivet_anrop` turning on sends a phone alert on the watchdog channel, with the same quiet hours. Deployed on ha-host at 17:58.
- ~~**B-078 · Spike: a Lovelace preview card (optional)**~~ — CLOSED 2026-11-08 (Sprint 03 T-19): see commit "T-19: Spike: a Lovelace preview card (optional)"
- ~~**B-079 · Unit-format helpers**~~ — CLOSED 2026-11-08 (Sprint 01 T-09): see commit "T-09: Unit-format helpers"
- ~~**B-080 · Text measurement and wrap utility**~~ — CLOSED 2026-11-08 (Sprint 01 T-08): see commit "T-08: Text measurement and wrap utility"
- ~~**B-081 · decision: relink the solar forecast in the owner's Energy settings**~~ — CLOSED 2026-11-08 at the owner's request. Open-Meteo Solar Forecast was installed and linked in the Energy prefs; `energy/solar_forecast` now returns hourly data. For the "expected solar today" role, bind `sensor.hemma_energy_production_today`. Details: H-54 in `<the maintainer's HA repo>`.
- ~~**B-082 · Rotate-image-token button per screen**~~ — CLOSED 2026-11-08 (Sprint 03 T-17): see commit "T-17: Rotate-image-token button per screen"
- ~~**B-083 · Scale YAML layouts to larger panels**~~ — CLOSED 2026-11-08 (Sprint 03 T-15): see commit "T-15: Scale YAML layouts to larger panels"
- ~~**B-084 · Area frames: rounded boxes and an inverted hero**~~ — CLOSED 2026-11-08 (Sprint 03 T-03): see commit "T-03: Area frames: rounded boxes and an inverted hero"
- ~~**B-085 · Header variants: masthead and title bar**~~ — CLOSED 2026-11-08 (Sprint 03 T-04): see commit "T-04: Header variants: masthead and title bar"
- ~~**B-086 · Inverted now panel (Tavlan)**~~ — CLOSED 2026-11-08 (Sprint 03 T-05): see commit "T-05: Inverted now panel (Tavlan)"
- [x] **B-087 · Widget-internal offsets scale with the panel** · 6h · prio P3 · src: Sprint 03 T-15 (returned part of B-083) · done 2026-11-09
      Grid geometry and type now scale (T-15). Widgets still place baselines with fixed px
      offsets (e.g. `r.y + 12`), so on TRMNL X (1872×1404) the now block's summary line
      overlaps the numeral and rows sit too tight (golden `tidslinjen_trmnl_x`). Route every
      widget offset through `theme.px()` and line heights through the type scale; verify with
      the TRMNL X golden of every layout.
      **Done 2026-11-09:** about 150 widget offsets, gaps, row heights and icon sizes go
      through `theme.px()`. The fixed TextStyle constants in widgets.py now come from the
      theme. Every 800×480 golden is pixel-identical (only `tidslinjen_trmnl_x` changed), and
      all 7 layouts were checked by eye at 1872×1404: no overlaps. The agenda's time column is
      sized to "heldag" too. Left unscaled on purpose: stroke widths, hairlines, 1–2 px bar
      insets, frame chrome, and the zero-config `build_now` screen (no theme).
- [x] **B-097 · Layout field: dropdown of bundled layouts and own files, free text allowed** · 1h · prio P2 · src: owner 2026-11-09 · done 2026-11-09
      Owner: "can we make "layout" a dropdown that shows the bundled layouts and a option to
      freetext?". SelectSelector with `custom_value: true`: bundled layouts first, then the
      user's layout and schedule files from /config/paperboard/, labelled. Test in
      test_subentry_flow.py.
- [x] **B-098 · Every role explains the value it expects** · 1h · prio P2 · src: owner 2026-11-09 · done 2026-11-09
      Owner: "each headline (Electricy price, solar power now, house power now etc) should have
      a info-circle that explain what type of value is expected". HA's config forms have no
      info-circle; the native mechanism is `data_description`, shown as help text under each
      field. All 18 roles, en + sv. A test fails if a role lacks a description in any language.
- [x] **B-100 · FOSS documentation standard** · 3h · prio P1 · src: owner 2026-11-09 · done 2026-11-09
      Owner: "the documentation in the code project must meet the high standard of FOSS, there
      should also be mentions that contributions are welcome and links to how to contribute".
      Added CONTRIBUTING.md, CODE_OF_CONDUCT.md (Contributor Covenant 2.1), SECURITY.md (GitHub
      private reporting), CHANGELOG.md (Keep a Changelog), issue forms and PR template,
      docs/configuration.md (every setting; the roles table is generated from strings.json),
      docs/README.md (index); README badges, a configuration link and a Contributing section.
      All local doc links checked.
- [x] **B-099 · decision: privacy scrub before the repository goes public** · 2h · prio P1 · needs: owner · src: B-100 review 2026-11-09
      Found 2026-11-09:
      - The children's first names are in room-sensor names in `tests/fixtures/states/owner_2026-11-08.json`
        and so in the "owner" goldens and **the README screenshots** (footer: "Sovrum a …").
        Calendar events are already anonymised.
      - `CLAUDE.md` (agent instructions: hosts ha-host/byos-host, paths, the commit address) and
        `docs/planning/`, `docs/research/` mention the owner's servers. They hold no secrets.
      Options: rename the rooms in the fixture and regenerate the goldens and README images;
      remove CLAUDE.md from the public tree (or .gitignore it); keep or drop the planning notes.
      History: the names are in earlier commits too, so going public needs either a fresh
      history (squash to one initial commit) or a history rewrite.
      **Done 2026-11-09 (owner: "CLAUDE.md and other claude-files should never get committed ...
      the same with persons names, addresses and similar, should not be committed and should be
      removed from history"):** history rewritten with git-filter-repo, keeping all 265 commits.
      - `CLAUDE.md` is removed from every commit and is now in `.gitignore`, with
        `CLAUDE.local.md` and `.claude/`.
      - Every PNG under `tests/golden/` and `docs/images/` is removed from history, then
        regenerated from the scrubbed fixture in one commit. 27 of the 41 images are
        pixel-identical; the rest differ only where names were.
      - Text and commit messages: person and room names, the street, the commit address,
        internal IPs, host names and private paths are replaced with neutral ones.
      - The full-history scan finds 0 matches afterwards.
- [x] **B-096 · Type scale on big panels: pixel fonts stop at 21 px** · closed 2026-11-09 by the owner, not done · 3h · prio P3 · src: B-087 review 2026-11-09
      On TRMNL X (scale 1.8) spacing grows but the TRMNL pixel fonts cap at 21 px, so small and
      medium text looks sparse and the "Imorgon" badge is a 56 px box around 21 px text.
      Option: above a scale threshold, map xs/s/m to Inter at scaled sizes (Inter is crisp at
      any size), keeping pixel fonts at 1.0. Verify with every TRMNL X layout; 800×480 goldens
      must stay identical.
- ~~**B-088 · First render after an HA start is 2–3.5 s**~~ — CLOSED 2026-11-08. Cause: resvg-py 0.5.0 **holds the GIL** for the whole render. Every render therefore froze HA's event loop (ha-host: 35 renders in 28 min, the slowest 5.1 s; HA logged Frigate "Updating state took" warnings at 18:04 and 18:10). Font loading is not the cost (0 ms); ha-host renders about 10× slower than dev-host and is loaded (load 3.7 on 4 cores, AppDaemon at 44 % CPU). Fix: resvg runs in one spawned worker process (`raster_worker.py`), started at setup. Main-thread stall on ha-host went from 560 ms to 22 ms per render (`scripts/check_worker_stall.py`). The budget is now 2,000 ms and the first render is not judged.
- ~~**B-089 · Device button steps through layouts**~~ — CLOSED 2026-11-08: a short press steps through all 7 layouts with a 30-minute hold; a double click resumes the schedule. Optional `cycle:`/`hold_minutes:` keys in the schedule file. Owner: "go, all 7, 30 minutes is fine".
- [x] **B-090 · Upstream: resvg-py releases the GIL** · 1h · prio P3 · src: B-088 · drafted 2026-11-09
      Draft an issue or PR for resvg-py (`py.allow_threads` around the render), with the
      measurement from `scripts/check_worker_stall.py`. The owner posts it. If upstream does it,
      the worker process can go.
      **Drafted 2026-11-09:** `docs/upstream/resvg-py-release-gil.md`, ready to paste. Checked
      `master`: there is still no `allow_threads`/`detach` in `svg_to_bytes`. **Waiting on the owner
      to post it.**
      **Parked 2026-11-09 (owner):** "lets park the image-library upstreaming ... i think we
      should do it, but other things are priotized now". It is an issue (a request), not a patch:
      we have no fork or changes to resvg-py.
- [x] **B-091 · Research: AppDaemon at 44 % CPU on ha-host** · 1h · prio P2 · src: B-088 (2026-11-08 18:30, `docker stats`) · done 2026-11-09
      Move to `<the maintainer's HA repo>` HASS-BACKLOG if confirmed: it is not paperboard's.
      **Done 2026-11-09, moved to hass H-58:** AppDaemon re-checks its app files every 1 s
      (`utility_delay`), and ha-host runs at 792 MHz (the VM host's BIOS lock, hass H-40). That gives
      a 2–3 s check and 65 % CPU. The same apps on dev-host: 3.5 %. Not paperboard's.
- [x] **B-092 · The render worker hung Home Assistant's shutdown** · 3h · prio P1 · src: live 2026-11-08 18:48–19:00 · done 2026-11-09
      After the upgrade to HA 2026.11.0, `homeassistant.restart` never finished. The last log line
      was "Found 3 non-daemonic threads", the ProcessPoolExecutor's threads. HA was down
      (502) for ~10 min until `docker restart homeassistant`. The worker is **off in production**
      (`USE_WORKER = False`, deployed 19:00), so renders stall the loop again (B-088's cause).

      Before it goes back on:
      - shut the pool down on `EVENT_HOMEASSISTANT_STOP` (not only on unload);
      - make the waiting daemonic, or use a plain `subprocess` worker with a pipe instead of
        `concurrent.futures`;
      - prove it with a real HA restart in a **throwaway** HA container that runs the integration.

      A unit test cannot catch this: the `hass` test fixture never runs HA's process exit.
      Also during the outage the old code answered `/api/display` with 500, which unpairs the
      panel; 8fc7be2 now answers 202.
      **Done 2026-11-09:** `raster_worker.py` is now a plain `subprocess.Popen` child speaking
      length-prefixed messages over stdin/stdout. It starts **no threads** (test), exits on EOF
      (so it dies with HA), and is stopped on `EVENT_HOMEASSISTANT_STOP` and on unload (off the
      loop). A dead or hung child (60 s) is killed and replaced on the next render.
      **Proof in a throwaway HA 2026.11.0 container on dev-host:** with the new worker,
      3 restarts via `homeassistant.restart` took 4.1 s each, with one child each time and no
      leftovers. **Control:** the old ProcessPoolExecutor version in the same container did
      not come back within 300 s and logged "Found 2 non-daemonic threads", the production
      symptom. Main-thread stall per render (`scripts/check_worker_stall.py`, dev-host):
      63 ms in-process, 2 ms with the worker. `USE_WORKER = True` again.
      Tests: test_raster_worker.py (5 new).
- [x] **B-095 · Normal text halfway to bold** · 1h · prio P1 · src: owner 2026-11-09 · done 2026-11-09
      Owner: "the normal thin test is hard to read ... can you increase the weight of normal
      text? not as much as bold text, but halfway there maybe". Inter Medium → SemiBold; pixel
      fonts drawn twice 1 px apart. See docs/design/rendering.md. Goldens and README images
      regenerated.
- [x] **B-094 · A known panel re-pairs without the window** · REVERSED 2026-11-09 by B-101 (HACS security review) · 1h · prio P1 · src: owner 2026-11-08 19:40 · done 2026-11-08
      Owner: "when i tried to reset (reboot) it factory reset, i do not like this process".
      `/api/setup` from a MAC the hub already paired, outside a window, re-binds it to its
      own screen with a fresh key (LAN-only). Trade-off in device-api.md setup case 4.
      Tests: test_setup_view.py (2 new).
- [x] **B-093 · Remember the last check-in across restarts** · 2h · prio P1 · src: live 2026-11-08 19:14 · done 2026-11-09
      `last_checkin` lives only in memory. After a restart it is None, and
      `binary_sensor.<screen>_missed_checkin` stays **off** forever if the device never comes
      back. That happened on 2026-11-08: the panel lost its pairing in the 18:48–18:59 outage
      and nothing alerted, so B-077's alert was blind.
      - Persist `last_checkin` with the device store.
      - Treat "no check-in for 3 polls since start-up" as missed as well.
      **Done 2026-11-09:** `last_checkin` and the refresh rate given in that answer are stored
      with the paired device (saved 30 s after a poll, flushed on unload) and restored at
      setup. The second bullet already held (the clock starts at setup).
      **Also fixed:** the missed-check-in allowance used the base rate (3 x 900 s), so with
      the night schedule (1 h polls) the alert turned on every night hour 22:45–04:45 on
      2026-11-08/09. It now uses 3 x the rate the device was last told.
      Tests: test_missed_checkin.py (3 new, all fail on the old code).
