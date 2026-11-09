# Security policy

## Supported versions

Security fixes go into the latest release. Please update before reporting.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Report it privately through GitHub:
[Security → Report a vulnerability](https://github.com/the-louie/paperboard/security/advisories/new).
Include what an attacker can do, the steps to reproduce, and the Paperboard and Home Assistant
versions.

You can expect an acknowledgement within 7 days. Once a fix is released, the advisory is
published with credit to you, unless you prefer otherwise.

## Scope and design

Paperboard serves an unauthenticated device API inside Home Assistant (the TRMNL firmware
cannot send Home Assistant credentials). How that API is protected is described in
[docs/design/device-api.md](docs/design/device-api.md):
- per-device keys;
- pairing only from the local network, inside a 5-minute window opened by an admin;
- unguessable image URLs.

Reports that break any of those guarantees are in scope.
