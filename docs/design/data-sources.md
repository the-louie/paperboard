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
