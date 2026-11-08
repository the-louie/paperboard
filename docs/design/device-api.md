# Device API: serving TRMNL from Home Assistant

## Route collision and auth under `/api` (T-03, 2026-11-08, HA 2026.11.0)

**Verdict: safe.** paperboard can register `/api/setup`, `/api/display` and `/api/log`.

- **No core route collides.**
  - A grep of `homeassistant` 2026.11.0 finds none of the three paths.
  - The nearest core routes are `/api/log_out` (`URL_API_LOG_OUT`), `/api/logbook` and
    `/api/error_log`, all distinct.
  - The only `/api/log` string in core is go2rtc's *own* server allow-list
    (`components/go2rtc/server.py:94`), on go2rtc's port, not HA's.
  - Pinned by `tests/test_http_assumptions.py::test_core_has_no_conflicting_routes` (http + api
    loaded). Re-run on every HA bump.
- **Unauthenticated views work under `/api`.** `HomeAssistantView.requires_auth = False` skips
  the Bearer/signed check in `helpers/http.py` `request_handler_factory`. The auth middleware
  only *marks* requests authenticated; it never rejects them.
- **Ban behaviour:**
  - HA's ip_ban counts a failed login only when the handler **raises** `HTTPUnauthorized`
    (`components/http/ban.py`, `ban_middleware`) or is wrapped in `@log_invalid_auth`.
  - A **returned** `web.Response(status=401/403)` is not counted.
  - Pinned by `test_unauthenticated_view_under_api`, threshold 2, 5 bad tokens, still not
    banned. The same test with `raise HTTPUnauthorized` fails, so the test can tell the two
    cases apart.
  - **Design rule:** the device views *return* 403 for a wrong token and never raise.
  - Brute force is countered by 256-bit tokens (`secrets.token_urlsafe(32)`) and
    constant-time compares (`hmac.compare_digest`), not by HA's ban. A per-IP failure
    counter in the view (B-073) can add a cooldown.
- **Compression:** `HomeAssistantView.json()` calls `enable_compression()` when the body is
  over 1024 bytes. aiohttp then gzips only if the client sends `Accept-Encoding: gzip`.
  - The firmware must not receive gzip.
  - Device views build `web.Response` directly and never call `enable_compression()`.
  - Pinned by the `Content-Encoding is None` assert.
- **Exposure:** the same views are reachable through every HA URL, including Nabu Casa remote
  UI and any reverse proxy. That makes them internet-facing whenever HA is. Mitigations
  (B-073):
  - `/api/setup` pairs only inside an owner-opened window;
  - per-device secret tokens;
  - the image path carries an unguessable token;
  - no state or entity data is ever returned, only image bytes and refresh metadata.
  - The README recommends pointing devices at the LAN URL.

No escape hatch is needed. If a future core release claims one of the paths, the fallback is a
firmware "custom server" base URL that includes a prefix, e.g. `http://ha:8123/paperboard`.
The firmware appends `/api/...` to its base URL; verify this in B-011.
