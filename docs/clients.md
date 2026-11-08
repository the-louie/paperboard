# Other image clients

TRMNL devices use the device API. Anything else that can fetch an image URL can show the same
screen.

- **Where the URL comes from:** the screen's image entity (`image.<screen>_screen_image`)
  carries `png_path` and `bmp_path` attributes. Prefix them with the Home Assistant URL the
  client can reach (LAN recommended).
- **Credentials:** the token in the path is the only one. Rotate it with the screen's
  **Rotate image link** button.

| Client | Use | Behaviour |
|---|---|---|
| ESPHome `online_image` | `png_path`, `format: PNG`, `type: BINARY` (1-bit profile) or `GRAYSCALE` | Sends `If-None-Match`; paperboard answers **304** while the frame is unchanged, so the ESP downloads only real changes. |
| Old TRMNL firmware, custom BMP readers | `bmp_path` | 1-bit BMP3, 800×480 = exactly 48 062 bytes (palette 0 = black). |
| TRMNL "Alias" plugin, LaraPaper, Terminus, other BYOS servers | `png_path` | Plain GET; `ETag`, `Content-Length` and `HEAD` are supported, and the response is never compressed. |
| Kindle / Kobo screensaver scripts | `png_path`, with the panel profile set to the device's model | The profile picks size and grey depth (4-bit for 8-bit panels). Rotation from the TRMNL model registry is not applied yet; rotate on the client. |

**Behaviour while a render is failing:** the last good image is served, with the
`X-Paperboard-Stale: 1` header. Before the very first frame: 503 with `Retry-After: 60`.
