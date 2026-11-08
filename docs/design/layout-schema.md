# Layout schema

## Validation library (Sprint 02 T-01, 2026-11-08)

**Decision:** layouts are validated with the `schema.py` shim. It uses **probatio** where HA
ships it (all 884 core config flows use it by 2026.11) and falls back to **voluptuous** on
older cores within our minimum (`hacs.json`: 2026.3.0).

- **Same API subset:** `Schema`, `Required`, `Optional`, `In`, `Range`, `All`, `Any`,
  `Coerce`.
- **Error paths:** both libraries carry `.path`. probatio reports **every** error in a file,
  voluptuous only the first. `schema.format_errors()` turns them into
  `widgets[1].area: expected str`. These strings go into the Repairs issue (B-029), so a
  layout author sees all problems at once on modern cores.
- **Rejected:**
  - plain dataclasses with hand-written checks: more code, worse messages;
  - pydantic: not a core dependency, and a pin would conflict with other integrations.

## Format (Sprint 02 T-02, 2026-11-08)

A layout is one YAML file:
- **Bundled:** `custom_components/paperboard/layouts/*.yaml`.
- **User's own:** `/config/paperboard/*.yaml`, which wins on a name clash.

It describes **where** widgets go, and with which **roles**. It never names an entity id: roles
are bound to entities once per home in the hub's options flow (B-032). The same file therefore
works in every home.

### Top level

| Key | Type | Meaning |
|---|---|---|
| `name` | str, required | Id used by the screen config (`layout:`). `[a-z0-9_]+`. |
| `title` | str | Shown in the screen config dropdown. |
| `canvas` | `[w, h]`, default `[800, 480]` | Design size in px. Other panels scale by `scale_factor` (B-064). |
| `grid` | map, required | See below. |
| `widgets` | list, required | See below. |
| `clock_resolution` | seconds, default 300 | How often the visible clock may change the image. |
| `lang` | `auto`/`sv`/`en`, default `auto` | `auto` follows HA's language. |

### Grid

```yaml
grid:
  columns: [250, fr]        # px, or fr = share of the remaining space
  rows: [40, fr, 154, 26]
  rules: 2                  # px width of black rules drawn between areas (0 = none)
  padding: [8, 16]          # inside each area: [vertical, horizontal] px
  areas:                    # one string per row, one name per column, '.' = empty
    - header   header
    - now      timeline
    - days     energy
    - footer   footer
```

- An area is the bounding box of all cells with that name. It must be rectangular, which is
  validated.
- **Reflow:** a widget that has nothing to draw returns `False`. Its area is then offered to
  the neighbour named by that widget's `collapse` option:
  - `collapse: left | right | up | down | none`;
  - the default is the horizontal neighbour sharing the full edge, else `none`.

  The neighbour is re-drawn into the merged rectangle. A collapsed area with `none` stays
  blank. Empty never means error.

### Widgets

```yaml
widgets:
  - type: header            # widget type from the widget library
    area: header
    options: {}             # type-specific; unknown keys are rejected
    collapse: none
```

| Type | Roles read | Key options |
|---|---|---|
| `header` | `calendars[]` (holiday names), `weather` (tomorrow 07) | `show_week`, `show_flag`, `badge: tomorrow_07 \| none` |
| `now` | `weather`, `outdoor_temp`, `indoor_temp`, `outdoor_humidity`, `wind`, `rain_today` | `rows: [indoor, feels_like, humidity, wind, dew_point, pressure, rain_today]` |
| `timeline` | `price`, `solar_forecast`, `weather` (hourly temperature) | `hours: 24`, `series: [solar_forecast, price, temperature]` (stacked in this order, one shared x-axis), `cheapest_hours: 2`, `night: dots \| none` |
| `hourly_table` | `weather`, `price` | `hours: 10`, `columns: [icon, temp, rain, wind, price]` |
| `daily` | `weather` | `days: 6`, `warn_gust_ms: 14`, `warn_rain_mm: 10` (a day over a threshold is inverted, and only then shows wind/rain) |
| `energy` | `price`, `solar_forecast`, `solar_power`, `house_power`, `grid_power`, `battery_soc` | `rows: [price_now, solar_expected_today, solar_now, house_now, battery]` |
| `energy_flow` | `solar_power`, `grid_power`, `battery_soc`, `battery_power`, `house_power` | figures beside the nodes (owner rule) |
| `rooms` | `rooms[]` | `columns: 1..3` |
| `stat` | any one role or `rooms[n]` | `label`, `unit`, `decimals`, `size: s..hero` |
| `sun_moon` | `sun` | — |
| `agenda` | `calendars[]` | `days: 7` |
| `text` | — | `template` (HA Jinja, text slots only), `size` |
| `footer` | the screen's own telemetry | `left: rooms \| name \| none` |

### Type scale (Sprint 02 T-03 implements it)

| Name | Font | px at scale 1.0 |
|---|---|---|
| `xs` | TRMNL12 | 12 |
| `s` | TRMNL16 | 16 |
| `m` | TRMNL21 | 21 |
| `l` | Inter | 26 |
| `xl` | Inter | 38 |
| `xxl` | Inter | 58 |
| `hero` | Inter | 74 |

Pixel fonts never scale fractionally. On a `scale_factor` 1.8 panel, `s` becomes TRMNL16 ×2
(integer upscaling), or the next pixel size, whichever is closer.

### Example: 01 Tidslinjen, with the owner's changes

```yaml
name: tidslinjen
title: Tidslinjen
grid:
  columns: [250, fr]
  rows: [40, 262, fr, 26]
  rules: 2
  padding: [8, 16]
  areas:
    - header header
    - now    timeline
    - days   energy
    - footer footer
widgets:
  - {type: header, area: header, options: {show_week: true, show_flag: true, badge: tomorrow_07}}
  - type: now
    area: now
    options: {rows: [indoor, feels_like, humidity, wind, rain_today]}   # no pressure (owner)
  - type: timeline
    area: timeline
    options: {hours: 24, series: [solar_forecast, price], cheapest_hours: 2, night: dots}
  - {type: daily, area: days, options: {days: 6}}
  - type: energy
    area: energy
    options: {rows: [price_now, solar_expected_today, solar_now, house_now, battery]}
  - {type: footer, area: footer, options: {left: rooms}}
```

### Example: 05 Tavlan, with the owner's changes

```yaml
name: tavlan
title: Tavlan
grid:
  columns: [290, fr]
  rows: [fr, 26]
  rules: 0
  areas:
    - now   table
    - now   footer
widgets:
  - type: now
    area: now
    options: {style: inverted, rows: [indoor, feels_like, humidity, wind, pressure, rain_today]}
  - {type: hourly_table, area: table, options: {hours: 10, then_days: 5}}
  - type: energy
    area: now
    options: {rows: [price_now, solar_expected_today, battery]}   # replaces "Huset nu · idag"
  - {type: footer, area: footer, options: {left: none}}
```

Two widgets may share one area when both are vertical stacks (`now` + `energy` above). The
area is split top to bottom in list order, each widget taking its natural height.

## Schedules (Sprint 03 T-06)

A layout file can instead be a **schedule** that picks one of the other layouts for each
render. The screen's `layout:` names the schedule.

```yaml
name: hallen
default: tidslinjen
schedule:
  - {layout: tavlan, from: "07:00", to: "08:00", days: weekdays, when: binary_sensor.skoldag}
  - {layout: almanackan, from: "22:00", to: "06:00", refresh_rate: 3600}
```

- **Matching:** entries are tried in order and the first match wins; nothing matching means
  `default`.
- **Time:** `from` is inclusive and `to` exclusive; a window may cross midnight. The part
  after midnight belongs to the start day, for `days` purposes.
- **`days`:** `all` (default), `weekdays`, `weekend`, or `[mon, tue, …]`.
- **`when`:** an entity that must be `on`. A missing or unavailable entity does not match:
  the safe default, so a broken school-day sensor never shows the school layout on a holiday.
- **Refresh:** `/api/display` shortens the device's `refresh_rate` so it wakes ~30 s after the
  next window boundary. An entry's own `refresh_rate` applies inside it (e.g. sleep at night).
- **Validation:** every named layout must exist (bundled, user YAML or built-in). Otherwise
  the schedule is rejected with a Repairs issue.
