# Rendering

## resvg-py spike (T-05, 2026-11-08)

**Go.** resvg-py 0.5.0 meets every rendering requirement.

| Measurement | Value | Where |
|---|---|---|
| Runs in the official HA container (Alpine 3.24, Python 3.14.10, x86_64), from its `cp310-abi3-musllinux_1_2` wheel | yes | deep research, `docker run --rm ghcr.io/home-assistant/home-assistant:stable`, 2026-11-08 |
| Dense 800×480 frame (~120 text runs, 24-bar chart, polyline, rules; denser than any mockup), median of 20 | **35.7 ms** | `scripts/spikes/spike_resvg.py`, local venv CPython 3.14.6, same wheel family (manylinux), 8-vCPU QEMU VM |
| Grey pixels before quantising, with `shape-rendering="crispEdges" text-rendering="optimizeSpeed"` | **0.0000** | same |
| 1-bit PNG of that frame (Pillow `optimize=True`) | **5 602 bytes** (16× under the 90 kB OG limit) | same |
| Full-frame time inside the HA container (research run, 25 text lines) | ~38 ms | research notes `rendering_engines.md` |

**Not repeated in a container this time.** The owner had the 3.56 GB HA image removed from
dev-host the same day. The container run in the research used the same resvg-py 0.5.0
wheel and the same flags. **aarch64 is still unverified** (wheel tags only); see B-070.

**Visual check:**
- TRMNL12/16/21 render on the pixel grid.
- Inter at 76 px without anti-aliasing reads cleanly at that size.
- Stroke-width 3 polylines and the filled bars stay solid.

The spike PNG is not committed; regenerate it with
`python scripts/spikes/spike_resvg.py <fonts> out.png`.

## Implications for the pipeline (B-008)

- Set `shape-rendering="crispEdges"` and `text-rendering="optimizeSpeed"` on the root `<svg>`.
  Then quantising is a pure palette mapping, with no dithering decision for vector content.
- resvg needs **TTF/OTF**, not WOFF2. Bundle `.ttf` files.
- With `font_dirs=[bundled]` and `skip_system_fonts=True`, output does not depend on the host.
  That is required for golden tests.
