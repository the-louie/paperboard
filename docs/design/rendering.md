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

## Text metrics: Pillow vs resvg (T-07, 2026-11-08)

`python -m scripts.spikes.spike_metrics` takes 5 strings with åäö, °, the − sign and
commas, across all 10 font/size pairs we use. It compares resvg's **advance width** (derived
from the ink shift between a start-anchored and an end-anchored copy) with Pillow's
`FreeTypeFont.getlength()`.

| Font | Sizes | max \|Δ advance\| |
|---|---|---|
| TRMNL12/16/21, Regular and Bold | 12, 16, 21 | **0.0 px** |
| Inter Medium/Bold/ExtraBold | 26, 38, 58, 74 | **≤ 0.8 px** |

**Decision:**
- Widgets measure with `FontRegistry.pillow(...).getlength(text)`, i.e. advance widths. That
  is what `text-anchor="end"` and column layout depend on.
- Right-aligned figures use `text-anchor="end"` in SVG, so resvg aligns them itself; Pillow is
  only needed for fitting and truncation.
- Ink bounding boxes differ by up to 11 px at 74 px, because Pillow's `getbbox` includes side
  bearings differently. Never use them for layout. Use advance plus the font's ascent and
  descent.
- A sub-pixel error of ≤ 0.8 px only shows on large Inter numerals, and those are never
  truncated. Leave a 1 px safety margin in fit calculations.

## Performance budget (T-29, 2026-11-08)

`python -m scripts.measure_layouts`: owner fixture, 20 renders each, on the dev-host VM
(8 vCPU QEMU), full pipeline (SVG build, resvg, quantise, PNG):

| Layout | Depth | Median | Max | Peak Python memory | PNG |
|---|---|---|---|---|---|
| status | 1-bit | 17 ms | 44 ms | 0.4 MB | 0.5 kB |
| now | 1-bit | 29 ms | 34 ms | 0.4 MB | 1.7 kB |
| proto_tidslinjen (densest mockup) | 1-bit | 64 ms | 74 ms | 0.5 MB | 6.3 kB |
| proto_tidslinjen | 2-bit | 80 ms | 93 ms | 0.8 MB | 6.9 kB |

- **Budget: 500 ms per frame.** The densest real design is 6–8× under it.
- Each renderer records `last_render_ms` and `max_render_ms` (in diagnostics) and logs **one**
  warning per run when a frame exceeds the budget.
- Rendering happens at most once per debounce (5 s) or tick (60 s), and only when the snapshot
  changed. At 80 ms that is < 0.2 % of one core in the worst case.
- **Not measured:** resvg's own native allocations (tracemalloc only sees Python), and an aarch64
  Pi. Re-run on a Pi in B-070.
