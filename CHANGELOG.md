# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Security
- The image link's token is no longer in the image entity's attributes (`png_path`,
  `bmp_path`), which every Home Assistant user can read and the recorder keeps. The links are
  now shown in the screen's **Reconfigure** dialog, for admins only. **If you used 0.1.0,
  press Rotate image link once:** the old token is in your recorder history.
- A panel that was paired before no longer re-pairs without the pairing window. Its MAC address
  was enough, and any device on the local network can see a MAC, take a key, read the
  dashboard and lock the real panel out. After a factory reset, press **Pair device** once.

## [0.1.0] - 2026-11-09

First public version.

### Added
- Rendering inside Home Assistant: no browser, no add-on, no cloud. Output is exact 1-, 2- and
  4-bit PNG for e-ink panels.
- 7 bundled layouts: Tidslinjen, Tidningen, Bento, Tavlan, TRMNL, Almanackan and Energi.
- Your own layouts and schedules as YAML files in `/config/paperboard/`. Changes are picked up
  within 30 s; errors show in Repairs.
- The TRMNL device API: pairing, image delivery, device logs. It supports TRMNL OG, TRMNL X
  and BYOD panels running TRMNL firmware, with 58 panel models detected automatically.
- An image URL for other clients: ESPHome, Kindle and others.
- Per screen: an image entity, and sensors for battery, Wi-Fi, firmware, last check-in and
  missed check-in.
- The device button steps through the layouts (30-minute hold); a double click returns to the
  schedule.
- Roles: pick once which entity is the weather, price, solar forecast and so on. Every role is
  optional, and each one explains the value it expects.
- The layout field is a dropdown of the bundled layouts and your own files, and also accepts
  a typed name.
- Swedish and English.

### Fixed
- Rendering no longer stalls Home Assistant: resvg runs in a separate process, without threads
  that could block Home Assistant's shutdown.
- The last check-in survives a restart. The missed-check-in alert follows the poll interval
  actually given to the device, so night schedules no longer trigger it.
- Widget spacing scales on large panels such as the TRMNL X.

[Unreleased]: https://github.com/the-louie/paperboard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/the-louie/paperboard/releases/tag/v0.1.0
