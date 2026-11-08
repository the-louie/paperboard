# Data sources

## Electricity price (Sprint 02 T-09, 2026-11-08)

The `price` role binds one **sensor**. An adapter turns it into a `PriceSeries`:

```python
PriceSeries(points=[PricePoint(start: datetime, end: datetime, value: float), ...],  # sorted
            unit="SEK/kWh", currency="SEK", includes_fees=bool | None,
            tomorrow_expected_at="13:00" | None)
```

| Source | How to recognise the bound entity | Data | Notes |
|---|---|---|---|
| **HACS `nordpool`** (custom-components/nordpool; **the owner's**, `sensor.nordpool_kwh_se3_sek_2_10_025`) | attributes `raw_today` / `raw_tomorrow` | lists of `{start, end, value}` with ISO times, here 96 quarter-hours, in the sensor's unit (SEK/kWh), **including** the configured fees and VAT. Also `today`/`tomorrow` (bare floats), `tomorrow_valid`, `currency`, `unit`, `price_in_cents`. | Measured on the owner's HA 2026-11-08: 96 × 15-min points, `tomorrow` empty before ~13:00. If `price_in_cents` is true, divide by 100. |
| **Core `nordpool`** (HA platinum integration) | entity's registry platform is `nordpool` | no price list on the entity. Call `nordpool.get_prices_for_date` with `config_entry` (from the entity's registry entry), `date` = today and tomorrow, `resolution` 15/30/60 → `{area: [{start, end, price}]}` | `price` is the **spot price per MWh in the entry's currency, without fees or VAT** (core `services.py:149-184`). Divide by 1000 for /kWh and mark `includes_fees=False`. An empty day returns `{area: []}`. |
| **ENTSO-e** (HACS `entsoe`) | attribute `prices_today` (or `prices`) as a list of `{time, price}` | hourly or 15-min, per kWh | End = next point's start (last point: + resolution). Verify against a real install in B-036; unverified here. |
| **Tibber** (core) | `tibber.get_prices` service | `{prices: {home: [{start_time, price}]}}` | Out of scope for B-036 (no test install). Add it on request. |
| Any other sensor | none of the above | the current state only | One-point series. The chart shows a single "now" bar, labelled. |

**Rules:**
- Display aggregates to **hourly** bars when the source is finer. This was agreed in the
  research (more readable at 800 px), and mockups 01, 04 and 08 use hourly bars.
- The cheapest-window search runs on the native resolution, from now to the end of the known
  data.
- "Tomorrow" appears when its points exist. Otherwise the chart ends at midnight and shows the
  "morgondagens pris kommer ~13:00" note. 13:00 CET is the Nord Pool day-ahead publication
  time; other sources set it to `None`.
- `includes_fees` is shown nowhere by default. It is passed on so a layout can label "spot"
  versus "total".

## Expected solar production (Sprint 02 T-11, 2026-11-08)

**The owner wants "Sol idag förväntat" everywhere, and an hourly curve on the price time axis.**

**Source:** the HA **energy platform contract**, the same one the Energy dashboard uses. An
integration that forecasts solar ships an `energy.py` with
`async_get_solar_forecast(hass, config_entry_id) -> {"wh_hours": {iso_start: wh}} | None`.
- core `forecast_solar`: `homeassistant/components/forecast_solar/energy.py` (read in the
  2026.11.0 venv);
- HACS Solcast implements the same contract.

core `energy` discovers it with
`async_process_integration_platforms(hass, "energy", ...)` (`energy/websocket_api.py:55-71`).

**How paperboard finds the config entry, with no extra role:**
1. Take the entity bound to `solar_forecast_today` (on the owner's HA:
   `sensor.energy_production_today`, 3.66 kWh on 2026-11-08).
2. Its entity-registry entry gives `platform` (`forecast_solar`) and `config_entry_id`.
3. `integration = await async_get_integration(hass, platform)`, then
   `platform_mod = await integration.async_get_platform("energy")`. This is the public loader
   API, not the integration's internals.
4. If `platform_mod` has `async_get_solar_forecast`, call it with that `config_entry_id` and get
   hourly Wh.
5. Sum today's points for "expected today", unless the bound sensor itself is the daily total.
   Then the sensor's state wins, because it is the number the owner sees elsewhere.

**Fallbacks, in order:**
- (a) Attributes on the bound sensor: Solcast `detailedHourly` / `detailedForecast`
  `[{period_start, pv_estimate}]` (kW). Verify on a real install before relying on it.
- (b) The bound sensor's state alone: the total only, no curve; the chart widget collapses.
- (c) Nothing bound: no solar anywhere; widgets collapse.

**Not used:** the `energy/solar_forecast` websocket. It depends on the Energy-dashboard
preferences, and on the owner's HA those point at a **removed** config entry (`dfa24fc0…`), so
it returns `{}` (measured 2026-11-08; B-081 / H-54). Going through the bound sensor's own config
entry works regardless of the Energy dashboard's state.

**Refresh:** forecast_solar updates hourly. Re-read every 30 min and on a state change of the
bound sensor.
