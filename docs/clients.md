# Other image clients

TRMNL devices use the device API. Anything else that can fetch an image URL can show the same
screen.

- **Where the URL comes from:** open the screen's **Reconfigure** dialog (admins only). It
  shows the PNG and BMP links, built from the hub's base URL. The links are deliberately not
  entity attributes: every user can read those, and the recorder keeps them.
- **Credentials:** the token in the path is the only one. Rotate it with the screen's
  **Rotate image link** button.

| Client | Use | Behaviour |
|---|---|---|
| ESPHome `online_image` | PNG link, `format: PNG`, `type: BINARY` (1-bit profile) or `GRAYSCALE` | Sends `If-None-Match`; paperboard answers **304** while the frame is unchanged, so the ESP downloads only real changes. |
| Old TRMNL firmware, custom BMP readers | BMP link | 1-bit BMP3, 800×480 = exactly 48 062 bytes (palette 0 = black). |
| TRMNL "Alias" plugin, LaraPaper, Terminus, other BYOS servers | PNG link | Plain GET; `ETag`, `Content-Length` and `HEAD` are supported, and the response is never compressed. |
| Kindle / Kobo screensaver scripts | PNG link, with the panel profile set to the device's model | The profile picks size and grey depth (4-bit for 8-bit panels). Rotation from the TRMNL model registry is not applied yet; rotate on the client. |

**Behaviour while a render is failing:** the last good image is served, with the
`X-Paperboard-Stale: 1` header. Before the very first frame: 503 with `Retry-After: 60`.

## Previewing in Home Assistant (Sprint 03 T-19)

No custom Lovelace card is needed (spike outcome). The built-in **picture-entity** card shows
the screen exactly as the panel gets it. It refreshes when the frame changes, because the image
entity bumps `image_last_updated`.

```yaml
type: picture-entity
entity: image.hallen_screen_image
show_state: false
show_name: false
```

To switch layouts, open the screen's **Reconfigure** dialog. A dropdown of bundled layouts is a
later nicety. A WYSIWYG editor (as in hass-eink-dashboard) is deliberately out of scope:
layouts are files, so they can be versioned and shared between homes.
