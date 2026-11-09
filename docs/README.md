# Documentation

## Using Paperboard
- [README](../README.md): what it is, install, first screen.
- [Configuration](configuration.md): the integration, roles, screens, schedules and layout files.
- [Layout and schedule format](design/layout-schema.md): every widget and option.
- [Other clients](clients.md): ESPHome, Kindle, TRMNL Alias, LaraPaper.

## How it works (design documents)
- [Rendering](design/rendering.md): SVG → resvg → exact 1/2/4-bit PNG, fonts, timings.
- [Device API](design/device-api.md): the TRMNL endpoints, pairing and the security review.
- [Data sources](design/data-sources.md): how forecasts, prices, solar and calendars are read.
- [Refresh policy](design/refresh-policy.md): when panels wake and why.
- [Testing](design/testing.md): golden images, the empty-house rule, the device emulator.

## Contributing
- [CONTRIBUTING.md](../CONTRIBUTING.md) · [Code of Conduct](../CODE_OF_CONDUCT.md) ·
  [Security policy](../SECURITY.md) · [Changelog](../CHANGELOG.md)

`planning/` and `research/` are the maintainer's working notes (backlog, sprints, the original
architecture research). They're kept for transparency; you don't need them to use Paperboard
or contribute to it.
