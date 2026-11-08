# Backlog — paperboard

Next ID: **B-088**

**Sources:**
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
- [ ] **B-063 · decision: decommission byos-host trmnl-byos and the screenshot cron** · 1h · prio P3 · needs: B-026, B-062 · src: V phase 3
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
- [ ] **B-071 · decision: release and HACS default PR** · 1h · prio P3 · needs: B-067, B-069, B-070 · src: N HACS rules
      The owner pushes, tags the release, and opens a PR to hacs/default.
- [ ] **B-072 · Upstream offer to cryptomilk** · 1h · prio P3 · needs: B-071 · src: R §build new
      Claude drafts an issue offering the device-API views; the owner posts it.

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
- [ ] **B-087 · Widget-internal offsets scale with the panel** · 6h · prio P3 · src: Sprint 03 T-15 (returned part of B-083)
      Grid geometry and type now scale (T-15). Widgets still place baselines with fixed px
      offsets (e.g. `r.y + 12`), so on TRMNL X (1872×1404) the now block's summary line
      overlaps the numeral and rows sit too tight (golden `tidslinjen_trmnl_x`). Route every
      widget offset through `theme.px()` and line heights through the type scale; verify with
      the TRMNL X golden of every layout.
- [ ] **B-088 · First render after an HA start is 2–3.5 s** · 2h · prio P3 · src: B-025 live deploy
      ha-host logged "Rendering Hallen took 2069 ms" and "3478 ms" (budget 500 ms), once per
      restart. Warm renders are not logged. Find out whether this is cold resvg/font setup or
      HA's busy start-up executor. Then warm up at setup, or skip the budget warning on the
      first render. Goal: no warning per restart (O3).
