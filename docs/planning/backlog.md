# Backlog — paperboard

Next ID: **B-082**

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
- → Sprint 01 T-25 (B-022 · Missed-check-in problem sensor)
- → Sprint 01 T-26 (B-023 · Widgets: "now" block and status footer)
- → Sprint 01 T-27 (B-024 · Diagnostics and redaction)
- [ ] **B-025 · decision: deploy to production HA (ha-host)** · 2h · prio P1 · needs: B-015, B-018, B-020, B-021, B-023 · src: CLAUDE.md working rules
      Copying to `/docker/hass/homeassistant/custom_components/` and restarting HA needs the
      owner's OK. Claude prepares the exact commands and a rollback, then verifies with the
      emulated client against production.
- [ ] **B-026 · decision: owner points the OG at HA** · 1h · prio P1 · needs: B-025 · src: V phase 1
      Done on the device or in the firmware portal (LAN URL, not Nabu Casa). byos-host's
      `trmnl-byos` stays as the fallback. Claude verifies the check-ins and telemetry.

## Phase 2 — Layout engine and the hard widgets (goal: mockup 01 live on real price, solar and weather data)

- [ ] **B-027 · Research: schema library for layouts** · 2h · prio P1 · src: R §risks 2 (voluptuous→probatio)
      Is voluptuous still OK for custom integrations on HA 2026.12+? Alternatives: probatio,
      plain dataclasses with explicit validation. The choice must give friendly error paths
      (`widgets[3].area`).
      Acceptance: the decision is recorded in `docs/design/layout-schema.md`.
- [ ] **B-028 · Design: layout YAML schema** · 4h · prio P1 · needs: B-027 · src: R §layout, N trmnl_protocol §(B)
      Covers:
      - grid (columns, rows, gutter);
      - areas;
      - the type scale (named sizes × `scale_factor`);
      - style tokens per bit depth;
      - widgets (type, area, options, `hide_if_empty`);
      - roles;
      - the schedule.

      Write it as a spec with mockups 01 and 05 as complete examples.
      Acceptance: the owner can read it and understand how 01 is built.
- [ ] **B-029 · Layout loader and validation** · 4h · prio P1 · needs: B-028 · src: R §layout
      - Reading: read `/config/paperboard/*.yaml` in the executor, and reload when a file
        changes (watch mtime).
      - Validation errors: a Repairs issue plus the last good layout. A bad file never blanks
        the screen.
      - Bundled layouts ship in the integration.

      Acceptance: tests for a bad file and a missing file.
- [ ] **B-030 · Grid engine with reflow** · 5h · prio P1 · needs: B-028 · src: R §layout
      Areas → pixel rectangles. A widget that reports "empty" collapses, and its neighbours in
      the same row or column take the space according to the rules in the spec.
      Acceptance: unit tests on geometry, plus a golden test of reflow.
- [ ] **B-031 · Type scale and style tokens** · 3h · prio P1 · needs: B-028 · src: N trmnl_protocol §TRMNL framework, V design rules
      - Named sizes map to a font and px: ≤21 px uses TRMNL bitmap fonts at native sizes,
        ≥26 px uses Inter.
      - Hatch and dot patterns for 1-bit; grey fills only at ≥2 bit.
      - Inversion style for warnings.

      Acceptance: a golden test of a style sheet.
- [ ] **B-032 · Roles: binding in config/options flow** · 5h · prio P1 · needs: B-013, B-028 · src: R §layout roles
      Roles: `weather`, `outdoor_temp`, `indoor_temp`, `price`, `solar_forecast`,
      `solar_power`, `grid_power`, `battery_soc`, `house_power`, `rooms[]` (name + entity),
      `calendars[]`, `sun`. Bound with entity selectors; every role is optional.
      Acceptance: flow tests, including "skip everything".
- [ ] **B-033 · Repairs for missing entities** · 3h · prio P1 · needs: B-032 · src: R §graceful degradation
      One issue per bound entity that is not in the registry. It clears itself when the entity
      returns. The screen is never blanked.
      Acceptance: tests for raise and clear.
- [ ] **B-034 · Data: weather forecasts** · 3h · prio P1 · needs: B-020 · src: N ha_integration_engineering §forecasts
      `weather.get_forecasts` (hourly and daily) with `return_response`, cached; refresh on a
      weather state change and every 30 min. It works when a type is not supported (e.g. no
      hourly).
      Acceptance: tests with a mocked service.
- [ ] **B-035 · Research: price sources** · 2h · prio P1 · src: N ha_integration_engineering §nordpool
      Compare:
      - the core `nordpool.get_prices_for_date`;
      - the HACS `nordpool` sensor attributes. The owner has
        `sensor.nordpool_kwh_se3_sek_2_10_025` with `today`/`tomorrow` as 96 quarter-hours
        including additional costs, and `tomorrow_valid`;
      - Tibber and ENTSO-e.

      Define a `PriceSeries` adapter interface: interval, currency, includes tax/fees.
      Acceptance: `docs/design/data-sources.md`.
- [ ] **B-036 · Price adapters** · 4h · prio P1 · needs: B-035 · src: B-035
      Two adapters: the core nordpool service, and a generic "sensor attribute list" (today and
      tomorrow, 15/60 min, hourly aggregation for display).
      Acceptance: tests with the owner's real attribute shape.
- [ ] **B-037 · Research: solar forecast source** · 2h · prio P1 · src: N ha_integration_engineering §energy
      How to get the hourly expected production without importing energy internals. Options:
      - the `energy/solar_forecast` websocket's backing function;
      - forecast_solar's `async_get_solar_forecast` → `wh_hours`;
      - Solcast attributes.

      The owner has Forecast.Solar (`sensor.energy_production_today`, 3.66 kWh on 2026-11-08).
      Acceptance: the chosen method is in `docs/design/data-sources.md`.
- [ ] **B-038 · Solar forecast adapter** · 3h · prio P1 · needs: B-037 · src: B-037
      Returns hourly Wh for today and tomorrow, and the expected total today ("Sol idag
      förväntat", which the owner wants everywhere).
      Acceptance: tests.
- [ ] **B-039 · TimeAxis object** · 3h · prio P1 · needs: B-030 · src: R §widgets (shared x-scale), V rules
      One shared scale (start, end, px per hour, now marker, ticks). Widgets placed in the same
      column share it.
      Acceptance: unit tests that time → x is identical across widgets.
- [ ] **B-040 · Widget: price chart** · 4h · prio P1 · needs: B-036, B-039 · src: M 01, M 08, V row 04 (filled/outline bars)
      - Bars: hourly bars, with past hours patterned.
      - Cheapest window: bracket plus label, and filled versus outlined bars per mockup 04.
      - Markers: a "now" line, min/max labels, and a "tomorrow ~13:00" note when tomorrow is
        missing.

      Acceptance: golden tests with full, empty and tomorrow-included data.
- [ ] **B-041 · Widget: solar forecast chart** · 3h · prio P1 · needs: B-038, B-039 · src: V rows 01 and 08
      An area or curve of expected production on the shared axis, stacked above or under the
      price chart.
      Acceptance: golden tests.
- [ ] **B-042 · Widget: hourly table (Tavlan)** · 4h · prio P2 · needs: B-034, B-036 · src: M 05
      Rows of time / icon / temperature / rain / wind / price bar; the "now" row inverted.
      Columns drop when their data is missing.
      Acceptance: golden tests.
- [ ] **B-043 · Widget: daily forecast with warning inversion** · 4h · prio P1 · needs: B-034 · src: V row 02
      Wind and rain are shown **only when they exceed** user thresholds (gust m/s, rain mm),
      and that day's cell is **inverted**.
      Acceptance: golden tests for a calm week and a stormy day.
- [ ] **B-044 · Weather icon set** · 3h · prio P1 · needs: B-031 · src: N rendering_engines, research (MDI at small sizes blurs)
      Pick and bundle a set of SVG weather icons that render crisp at 20/28/40 px in 1-bit:
      MDI (Apache-2.0) at sizes snapped to its 24-px grid, or another set. Map every HA
      condition.
      Acceptance: a golden sheet of all conditions at 3 sizes.
- [ ] **B-045 · "Empty house" gate** · 2h · prio P1 · needs: B-030, B-040 · src: R §graceful degradation
      One test that renders every widget and every bundled layout with zero entities and
      asserts no exception plus a golden PNG. CI blocks on it.
- [ ] **B-046 · Layout 01 Tidslinjen with the owner's changes** · 3h · prio P1 · needs: B-023, B-040, B-041, B-043 · src: V row 01, M 01
      The changes: no "Tryck"; the solar forecast graph replaces the temperature/sun graph, on
      the same time axis as the price graph.
      Acceptance: the golden test matches the agreed look; deployed after B-025.

## Phase 3 — Remaining widgets and the schedule (goal: all 8 mockups in rotation, night sleep)

- [ ] **B-047 · Widget: energy flow** · 5h · prio P2 · needs: B-031, B-032 · src: V row 08 (addition)
      Nodes for sun, grid, battery and house; absent nodes and their edges are dropped.
      Figures sit **beside** the nodes: grid above, sun to the right with its label to the
      left, battery above.
      Acceptance: golden tests with all nodes, with no battery, and with no solar.
- [ ] **B-048 · Widget: room list** · 2h · prio P2 · needs: B-006, B-031 · src: M 02/03/06
      1–3 columns, figures right-aligned by measured width, "—" per missing room.
- [ ] **B-049 · Widget: calendar agenda** · 4h · prio P2 · needs: B-032 · src: M 07
      `calendar.get_events` (cached), grouped per day, truncation by measured width, "No
      events" or collapse.
- [ ] **B-050 · Widget: sun and moon** · 2h · prio P3 · needs: B-031 · src: M 04/07
      Sunrise and sunset from the `sun` entity, day length and its delta, moon phase computed
      locally (never missing).
- [ ] **B-051 · Widget: stat / key-value** · 3h · prio P1 · needs: B-031 · src: M 03/06
      A generic value with label, unit, format and precision, plus `sv`/`en` decimal commas.
- [ ] **B-052 · Widget: headline/prose text slot** · 3h · prio P3 · needs: B-031 · src: M 02, R §Jinja only in text slots
      HA Jinja is rendered per slot in the loop, under try/except, with a timeout. The text is
      wrapped by measured width.
- [ ] **B-053 · Layout 02 Tidningen** · 2h · prio P2 · needs: B-043, B-048, B-052 · src: V row 02
      Add "Sol idag förväntat" under ENERGI; warning inversion in the forecast row.
- [ ] **B-054 · Layout 03 Bento** · 2h · prio P2 · needs: B-048, B-051 · src: V row 03
      Remove "mot igår"; expected solar today under ENERGI.
- [ ] **B-055 · Layout 05 Tavlan** · 2h · prio P2 · needs: B-042 · src: V row 05
      Expected solar today instead of "Huset nu · idag". Intended for 07–08 on school days.
- [ ] **B-056 · Layout 06 TRMNL** · 2h · prio P3 · needs: B-051 · src: V row 06
      Expected solar today.
- [ ] **B-057 · Layout 07 Almanackan** · 2h · prio P3 · needs: B-049, B-050 · src: V row 07
      "Uterum" last in its row.
- [ ] **B-058 · Layout 08 Energi** · 2h · prio P2 · needs: B-040, B-041, B-047 · src: V row 08
      Solar forecast chart directly under the price chart (shared axis) instead of the weather;
      flow figures beside the nodes.
- [ ] **B-059 · Layout 04 Instrument (bar-chart parts only)** · 1h · prio P3 · src: V row 04
      The owner rejected the gauges. Only check that the filled/outlined bar style is
      available in B-040; no layout ships.
- [ ] **B-060 · Schedule: time-of-day layouts** · 4h · prio P1 · needs: B-029 · src: R §schedule, V Times of day
      Schedule windows (time range, weekday or workday condition via a binary_sensor, layout,
      refresh_rate). `/api/display` picks the layout per poll, and `refresh_rate` aims at the
      next switch.
      Acceptance: time-travel tests.
- [ ] **B-061 · Night sleep and refresh policy** · 2h · prio P2 · needs: B-060 · src: N trmnl_protocol §refresh
      A long refresh_rate at night, the TRMNL full-refresh cadence (every 8th update) documented,
      and the battery impact measured from the telemetry.
- [ ] **B-062 · decision: which layout when** · 1h · prio P2 · needs: B-060 · src: V
      The owner picks the schedule.
- [ ] **B-063 · decision: decommission byos-host trmnl-byos and the screenshot cron** · 1h · prio P3 · needs: B-026, B-062 · src: V phase 3
      After one stable week. Claude prepares the steps, and the owner OKs them.

## Phase 4 — Other panels (goal: a second panel type from the same layouts)

- [ ] **B-064 · Panel profiles from the TRMNL model table** · 4h · prio P3 · src: N trmnl_protocol (61 models, scale_factor)
      Resolution, bit depth, rotation, byte limit and scale_factor; the profile is chosen from
      the `Model` header automatically, with a manual override.
- [ ] **B-065 · 2-bit and 4-bit render paths** · 4h · prio P3 · needs: B-064 · src: R §engines
      Grey fills enabled at ≥2 bit; golden tests per depth.
- [ ] **B-066 · Generic image clients** · 3h · prio P3 · needs: B-018 · src: R §serving (Alias, ESPHome online_image, Kindle, LaraPaper)
      Document and test the token URL with the ESPHome `online_image` ETag behaviour and BMP
      output for old firmware.

## Phase 5 — Publish (goal: a public HACS install another home can configure with no code)

- [ ] **B-067 · README and documentation** · 5h · prio P2 · src: R §HACS publishing
      Install, configuration, layout reference, a widget catalogue with images, and FAQ
      ("works without sensor X").
- [ ] **B-068 · Brand assets** · 1h · prio P3 · src: N ha_integration_engineering §brand
      `custom_components/paperboard/brand/icon.png` and `logo.png` (HA ≥ 2026.3).
- [ ] **B-069 · CI workflow** · 3h · prio P2 · needs: B-045 · src: R §testing
      GitHub Actions: hassfest, the HACS action, ruff, pytest, golden images, empty house.
      Verify the action input names (the research did not).
- [ ] **B-070 · Research: aarch64 verification** · 2h · prio P2 · src: R §risks 4
      Run resvg-py in the aarch64 HA image under qemu (`docker run --platform linux/arm64`) and
      render a golden fixture.
      Acceptance: the result is recorded; a mismatch blocks release.
- [ ] **B-071 · decision: release and HACS default PR** · 1h · prio P3 · needs: B-067, B-069, B-070 · src: N HACS rules
      The owner pushes, tags the release, and opens a PR to hacs/default.
- [ ] **B-072 · Upstream offer to cryptomilk** · 1h · prio P3 · needs: B-071 · src: R §build new
      Claude drafts an issue offering the device-API views; the owner posts it.

## Cross-cutting

- → Sprint 01 T-28 (B-073 · Security review of the device endpoints)
- → Sprint 01 T-29 (B-074 · Performance budget)
- [ ] **B-075 · Localisation of widget texts** · 3h · prio P3 · needs: B-051 · src: M (Swedish), HACS audience
      Weekday and month names, units, decimal separator per HA language (sv, en).
- ~~**B-076 · Fixture capture script**~~ — CLOSED 2026-11-08 (Sprint 01 T-12): see commit "T-12: Fixture capture script"
- [ ] **B-077 · Device liveness → owner alert** · 1h · prio P2 · needs: B-022, B-025 · src: O4 in <the maintainer's HA repo>
      Add the problem sensor to the owner's AppDaemon watchdog or notification path (that
      change is made in the `<the maintainer's HA repo>` repo).
- [ ] **B-078 · Spike: a Lovelace preview card (optional)** · 3h · prio P3 · src: R (the cryptomilk editor is a card)
      Only a read-only preview of the ImageEntity with a layout picker; no WYSIWYG editing.
- ~~**B-079 · Unit-format helpers**~~ — CLOSED 2026-11-08 (Sprint 01 T-09): see commit "T-09: Unit-format helpers"
- ~~**B-080 · Text measurement and wrap utility**~~ — CLOSED 2026-11-08 (Sprint 01 T-08): see commit "T-08: Text measurement and wrap utility"
- [ ] **B-081 · decision: relink the solar forecast in the owner's Energy settings** · 1h · prio P1 · src: Sprint 01 T-13
      The `energy/solar_forecast` websocket returns `{}`. The energy prefs point at config entry
      `dfa24fc0…`, which no longer exists, while the loaded forecast_solar entry is `01KSDE…`
      ("Hemma"). The owner relinks it in Settings → Energy → Solar panels →
      Forecast. Without this, the HA energy dashboard has no forecast, and B-037/B-038 have no
      hourly data to test against. Mirrored as H-54 in `<the maintainer's HA repo>`.

