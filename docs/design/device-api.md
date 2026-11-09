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

## The owner's device (T-04, 2026-11-08, read-only from byos-host's trmnl-service)

Read from `http://127.0.0.1:3077/status.json` and the container log on byos-host. The MAC is
deliberately not recorded here.

| Header / fact | Value | Consequence |
|---|---|---|
| `Model` | **`xiao_epaper_display`** | The device is **not a TRMNL OG**. It is a Seeed XIAO 7.5" ePaper panel running TRMNL firmware. Panel profiles must key on `Model`, and B-064 moves earlier in priority. |
| `FW-Version` | **1.8.10** | ≥ 1.6.0, so 2-bit PNG is supported per the protocol notes. ≥ 1.5.2, so 1-bit PNG with partial refresh works. |
| `Width` × `Height` | 800 × 480 | Same canvas as the OG. |
| `Battery-Voltage` | 4.20 V on every check-in | It sits on USB power (the photo shows a cable), so the voltage is a flat line. The battery % sensor stays useful for other homes. |
| `RSSI` | −55 to −58 dBm | Good. |
| `Refresh-Rate` | 900 s | Matches trmnl-service's `REFRESH_RATE: "900"`. |
| `WiFi-Band` | 2.4 | Extra header, not in the protocol notes; record it as telemetry. |
| `Wake-Time` | ~5374 ms | Extra header; useful for diagnostics. |
| `Image-Cached` | false | |
| Image served today | png1, 3–5 kB | 18× under the 90 kB OG limit. |
| Byte limit | **not yet confirmed** | The XIAO ESP32-S3 has PSRAM, which would make it the 750 kB class. Verify against the firmware's board table in B-064; until then, keep the 90 kB OG limit. |
| `Access-Token` | sent (`d506…`) | trmnl-service runs with `api_key_required: false`, so it is not checked today. |

## Pairing (T-14, 2026-11-08)

### What the firmware does

Sources: research notes (firmware `5246feb`, 1.8.19) and the owner's working trmnl-service
(`<the maintainer's earlier TRMNL server>`), which runs the owner's device today.

- **Setup:** `GET <base>/api/setup` is sent **only while the device has no API key**. It sends
  `ID` (MAC), `FW-Version`, `Model`, `Width`, `Height` and `RSSI`, and **no Access-Token**.
- **Setup response:** the JSON `status` must be **200**, or setup fails and the device retries.
  On 200 it stores `api_key` and `friendly_id`, then fetches `image_url`.
  - Older firmware insists on a **1-bit BMP** setup image of exactly 48 062 bytes (800×480).
    trmnl-service serves a BMP from setup for every firmware version.
- **`/api/display` with JSON `status: 500`:** the firmware drops its key, polls again soon and
  **re-runs setup**. trmnl-service relies on this for bad tokens (comment at `server.py:286`).
  - The hosted TRMNL returns 500 + `reset_firmware: true` instead. That is a full reset;
    **never send `reset_firmware`**.
- **JSON `status: 202`:** "not registered", fast-poll, no re-setup.
- **Base URL:** the firmware appends `/api/...` literally to its base URL, so a base URL with a
  path prefix works. That is the escape hatch if core ever takes these paths.

### paperboard's flow

1. **Pairing window:** the owner adds a Screen (config subentry) and presses
   `button.<screen>_pair`, which opens a **5-minute** window for that screen. One window per
   hub at a time; a second press restarts it.
2. **Setup in the window:** while the window is open, the first `/api/setup` with an `ID` gets:
   - a new `api_key = secrets.token_urlsafe(32)`, stored in the subentry data together with the
     MAC;
   - `friendly_id` = the first 6 hex characters of sha256(MAC), uppercase, as trmnl-service
     does;
   - `image_url` pointing at a **BMP** variant of the current frame;
   - `{"status": 200, "message": "Paired with <screen name>"}`.

   The window then closes.
3. **Setup outside the window:** `{"status": 404, "message": "Pairing is closed. Press
   Pair on the screen in Home Assistant."}` with HTTP 200. The firmware treats it as a failed
   setup and retries later, so a device can be paired *after* it starts polling.
4. **Known MAC, no window:** treated like any other setup outside the window (case 3). A MAC
   is visible to every device on the LAN, so it is not a credential. From 2026-11-08 to
   2026-11-09 (B-094) a known MAC re-paired without the window; the HACS review showed that
   any LAN device could then take a key, read the dashboard and lock the real panel out, so
   it was removed (B-101). After a factory reset the owner presses Pair device once.
4. **`/api/display` with a missing, unknown or wrong `Access-Token` for that `ID`:** HTTP 200
   `{"status": 500, "message": "unknown device, re-running setup"}`, **without**
   `reset_firmware`. The device then re-runs setup, which works only inside a window. This is
   also the migration path from trmnl-service, whose MAC-derived key paperboard does not know.
   - It is returned, never raised, so HA's ip_ban is untouched (T-03).
   - Each such event updates a diagnostic "last rejected device" with MAC, time and IP. A
     Repairs issue is raised when an unknown MAC polls more than 10 times in an hour.
5. **Re-pair:** pressing Pair on a screen that already has a device replaces the binding at
   the next setup. The old key stops working at once.

The device was rejected with JSON status 500 rather than HTTP 403. T-03's
"return 403" rule still applies to the **image** URL. On `/api/display`, the JSON status is
what drives the firmware, so the HTTP status stays 200 there, as trmnl-service and the hosted
service do.

### Open: verify on the real device in B-026

- Does switching the base URL in the captive portal clear the stored key? If not, path 4
  covers it.
- That 1.8.10 accepts a PNG setup image (if so, BMP is only kept for old firmware).

## Security review (T-28, 2026-11-08)

| Surface (all `requires_auth=False`) | Who can call it | What it returns | Controls |
|---|---|---|---|
| `GET /api/setup` | anyone who can reach HA | a device key, **only** inside an owner-opened 5-min window, **only** from a LAN/loopback address and never through Nabu Casa (`is_cloud_connection`), single use | Outside those conditions: JSON 404, no state. `request.remote` honours HA's `use_x_forwarded_for` for trusted proxies. |
| `GET /api/display` | anyone | image URL + refresh rate for a paired device; otherwise JSON 500 (no state, no hint whether the MAC exists) | ID + 256-bit key, `hmac.compare_digest`. No HA data in the body. |
| `POST /api/log` | anyone | 204 / 403 / 400 / 413 | Same auth as display; body ≤ 64 kB, ≤ 50 entries, fixed field allow-list. |
| `GET/HEAD /api/paperboard/image/{screen}/{token}/{file}` | anyone holding the URL | the screen's PNG/BMP | 256-bit per-screen token in the path, constant-time compare, 403/404 returned not raised. |

- **Brute force:** 2²⁵⁶ keys. HA's ip_ban is deliberately not fed (T-03), because a
  misconfigured panel would otherwise get the owner's own IP banned. No separate rate limiter:
  every rejected request costs one dict lookup and one HMAC compare, with no rendering, I/O or
  logging.
- **Rendering is never on a request path**, so unauthenticated requests cannot trigger CPU work.
- **Data exposure:**
  - The image itself contains home data (temperatures, calendar); that is its purpose. Anyone
    with the image URL sees it.
  - The token sits in the URL path, so it can appear in reverse-proxy access logs. HA itself
    does not log request paths at INFO.
  - **Rotate:** the screen's **Rotate image link** button mints a new token (B-082).
  - **Where the token is shown:** only in the screen's Reconfigure dialog, which needs admin.
    It is never an entity attribute: those are visible to every user and kept in the
    recorder (B-101).
- **Logging hygiene:** the integration logs only render failures (screen name + error). It
  never logs headers, keys, tokens or MACs. Diagnostics redact keys and tokens and reduce MACs
  to their last two octets (T-27). Every known token, key and full MAC is also replaced
  inside free text (device log lines), the base URL is redacted, and a rejected device's IP
  becomes "local" or "remote".
- **Nabu Casa / internet exposure:** the device endpoints are reachable wherever HA is. After
  pairing that is harmless (keys required). Pairing itself is LAN-only. The README must say:
  point devices at the LAN URL.
  - **Proxies:** a reverse proxy that HA is not configured for makes every caller look like
    the proxy's LAN address. So the client addresses in `X-Forwarded-For`, `X-Real-IP`,
    `Forwarded`, `CF-Connecting-IP` and `True-Client-IP` must be local too; an unparsable one
    counts as not local, and a refusal logs one warning naming the forwarded address.
- **Stored secrets:**
  - Device keys live in `.storage/paperboard.<entry>.devices`.
  - Image tokens live in the config subentry (`.storage/core.config_entries`).
  - Both are in HA backups, like every other integration secret.
- **Not covered:**
  - TLS: the firmware does not verify certificates, per the research.
  - A hostile LAN device inside an open pairing window: it can take the pairing, and the
    owner sees the wrong friendly ID on the panel. The window is 5 minutes, single use, and
    opened by an admin action.
  - A hostile LAN device spoofing an already-paired MAC outside a window gets nothing: setup
    case 4 (B-101).
