# Configuring Paperboard

Paperboard is configured in three layers. The first two are forms in Home Assistant; the
third is optional YAML files for anything the forms can't express.

| Layer | Where | Applies to |
|---|---|---|
| 1. The integration | Settings → Devices & services → Paperboard → **Configure** | every screen |
| 2. Screens | the **Add screen** button on the Paperboard integration | one panel each |
| 3. Files | `/config/paperboard/*.yaml` | the screens that name them |

## 1. The integration

**Configure → Paperboard settings:**
- **Base URL:** the address your panels use to reach Home Assistant. Use the LAN address
  (e.g. `http://192.168.1.10:8123`), not a cloud URL: pairing only works from the local
  network.
- **Default refresh interval:** how often a panel asks for a new image, in seconds.
  Screens can override it.

**Configure → Sensors and data (roles):** a *role* says what an entity means in your home.
Every layout reads the same roles, so you pick each sensor once, not per dashboard.
- **Every role is optional.** Leave a role empty if your home doesn't have it. The parts of a
  layout that need it are left out, and their neighbours take the space.
- **Help text:** each field in the form explains the value it expects.
- **Missing entities:** if a bound entity later disappears, a Repairs issue tells you which one.

| Role | What it expects |
|---|---|
| **Weather (forecast)** (`weather`) | A weather entity with forecasts (for example weather.home, SMHI or Met.no). Gives the current condition, today's high and low, and the hourly and daily forecasts. |
| **Outdoor temperature** (`outdoor_temp`) | Outdoor temperature sensor (°C), for example your own weather station. Shown as the big number; without it the weather entity's temperature is used. |
| **Second temperature (e.g. conservatory)** (`indoor_temp`) | Any other temperature sensor (°C), shown as one row next to the outdoor temperature, for example a conservatory or a porch. |
| **Outdoor humidity** (`outdoor_humidity`) | Outdoor relative humidity sensor (%). |
| **Rain today** (`rain_today`) | Rain so far today (mm): a daily total that resets at midnight, usually from a weather station. |
| **Electricity price** (`price`) | Electricity price now, per kWh, whose attributes hold the hourly prices: Nord Pool (core or HACS) or ENTSO-e. The price chart needs today's prices, and tomorrow's once they are published (around 13:00 for Nord Pool). |
| **Expected solar energy today** (`solar_forecast_today`) | Expected solar energy today (kWh) from a forecast integration that feeds the Energy dashboard (e.g. Forecast.Solar or Open-Meteo Solar Forecast); Solcast is read from its attributes. The hourly curve is read from the same integration. |
| **Solar power now** (`solar_power`) | Solar production right now (W or kW), the PV power from your inverter. |
| **Grid power now** (`grid_power`) | Power to or from the grid right now (W or kW). Expected: import (buying) is positive. If your meter shows export as positive, tick the box at the bottom. |
| **House power now** (`house_power`) | The whole house's consumption right now (W or kW). |
| **House energy today** (`house_energy_today`) | The house's consumption so far today (kWh): a daily total that resets at midnight. |
| **Home battery charge** (`battery_soc`) | Home battery state of charge (%, 0–100). |
| **Home battery power** (`battery_power`) | Home battery power right now (W or kW), charging or discharging. Either sign convention works: the size is shown. |
| **Sun** (`sun`) | The sun entity (normally sun.sun): sunrise, sunset and the night shading on the time axis. |
| **Room temperatures** (`rooms`) | Indoor temperature sensors (°C), one per room, shown as a list or a status line. |
| **Calendars** (`calendars`) | Calendar entities whose events are shown in the agenda and the week view. |
| **Feels-like temperature** (`feels_like`) | Feels-like (apparent) temperature sensor (°C), usually from a weather station. |
| **Grid meter reports export as positive (e.g. Huawei)** (`grid_export_positive`) | Tick if the grid sensor above shows export (selling) as a positive number, as Huawei meters do. Leave unticked if import is positive. |

## 2. Screens

Each screen is one physical panel (or one image URL). **Add screen** asks for:
- **Name:** shown in Home Assistant and used for the entity names.
- **Panel:** leave it on *Automatic*. Paperboard then follows the model the device reports,
  from 58 TRMNL models plus Kindle and BYOD panels. Pick a model only for a client that
  doesn't report one.
- **Layout:** a dropdown of the bundled layouts and your own files from layer 3. You can also
  type a name, for a file you are about to create.
- **Refresh interval:** overrides the integration's default for this screen.

Each screen gets a **Pair device** button. After you press it, you have 5 minutes to point
the panel at the base URL; see the README's
[Set up a screen](../README.md#set-up-a-screen) section. Each screen also gets an image entity
and sensors for battery, Wi-Fi signal, firmware, last check-in and missed check-in. The missed
check-in alert turns on after three missed polls.

**Two or more panels:** add one screen per panel. Each screen can use its own layout or
schedule. They share the roles from layer 1, so for example the list of rooms is the same on
every panel.

## 3. Files in `/config/paperboard/`

Paperboard reads every `*.yaml` file in that folder and checks for changes every 30 s; no
restart is needed. If a file has an error, a Repairs issue names it, and the last working
version keeps rendering. There are two kinds of file.

### Schedules: which layout to show when

```yaml
name: hallen                 # the name you pick in the screen's Layout field
default: tidslinjen          # shown when no entry matches
schedule:                    # first match wins
  - {layout: tavlan, from: "06:30", to: "08:00", days: weekdays}
  - {layout: tidslinjen, from: "23:00", to: "06:00", refresh_rate: 3600}  # sleep 1 h at night
cycle: [tidslinjen, tavlan, energi]   # optional: layouts the device button steps through
hold_minutes: 30                      # optional: how long a button choice is held
```

An entry can also have `when:` with an entity id, so it only applies while that entity is
`on`, for example a school-day sensor. Panels wake up just after a schedule boundary, so the
switch happens on time.

### Layouts: your own dashboard design

A layout is a grid of named areas, each filled by a widget: now, timeline, daily forecast,
hourly table, energy flow, agenda, rooms and others. The full format, with examples, is in
[design/layout-schema.md](design/layout-schema.md). The bundled layouts in
`custom_components/paperboard/layouts_yaml/` are good starting points: copy one, change its
`name:`, and edit it.

## The device button

On TRMNL hardware, a short press of the button shows the next layout in the cycle for
`hold_minutes` (30 by default). A double click goes back to the schedule. Details:
[design/layout-schema.md#the-device-button-b-089](design/layout-schema.md#the-device-button-b-089).
