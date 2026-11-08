"""T-05 spike: render a dense mockup-like SVG with resvg-py and measure it.

Usage: python scripts/spikes/spike_resvg.py <font_dir> [out.png]

Prints: frame time (median of 20), share of grey pixels before quantising, and the
1-bit PNG size. Not shipped; kept for re-measuring after resvg-py upgrades.
"""

import io
import statistics
import sys
import time

import resvg_py
from PIL import Image


def dense_svg() -> str:
    """About 120 text runs, a 24-bar chart, a polyline and rules: denser than any mockup."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="480" '
        'shape-rendering="crispEdges" text-rendering="optimizeSpeed">',
        '<rect width="800" height="480" fill="#fff"/>',
        '<text x="18" y="27" font-family="TRMNL21" font-weight="bold" font-size="21">'
        "Söndag 8 november · v. 45 · Fars dag</text>",
        '<line x1="0" y1="38" x2="800" y2="38" stroke="#000" stroke-width="2"/>',
        '<text x="18" y="140" font-family="Inter" font-size="76">3,1°</text>',
    ]
    for i, (k, v) in enumerate([("Uterum", "5,7°"), ("Känns som", "3,1°"), ("Fukt", "89 %"),
                                ("Vind", "0,5 (1,5) m/s SO"), ("Regn idag", "0,0 mm")]):
        y = 175 + i * 18
        parts.append(f'<text x="18" y="{y}" font-family="TRMNL16" font-size="16">{k}</text>')
        parts.append(f'<text x="230" y="{y}" font-family="TRMNL16" font-weight="bold" '
                     f'font-size="16" text-anchor="end">{v}</text>')
    for h in range(24):
        x = 280 + h * 21
        bar = 20 + (h * 37 % 60)
        parts.append(f'<rect x="{x}" y="{220 - bar}" width="18" height="{bar}" fill="#000"/>')
        parts.append(f'<text x="{x}" y="240" font-family="TRMNL12" font-size="12">'
                     f"{(10 + h) % 24:02d}</text>")
    pts = " ".join(f"{280 + h * 21},{90 - (h * 13 % 40)}" for h in range(24))
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#000" stroke-width="3"/>')
    for d in range(6):
        x = 20 + d * 70
        for j, txt in enumerate(["Mån", "5°", "3°", "1,8 mm"]):
            size = 21 if j == 1 else 16
            parts.append(f'<text x="{x}" y="{330 + j * 22}" font-family="TRMNL{size}" '
                         f'font-size="{size}">{txt}</text>')
    for r in range(8):
        parts.append(f'<text x="450" y="{320 + r * 18}" font-family="TRMNL16" font-size="16">'
                     f"Rum {r} 20,{r}° · sol 0,2 kW · el 1,89 kr</text>")
    parts.append('<text x="18" y="472" font-family="TRMNL12" font-size="12">'
                 "Inne: Kök 20,9° · Tv-rum 19,7° · Hallen 20,7° · 2026-11-08 10:05</text>")
    parts.append("</svg>")
    return "".join(parts)


def grey_share(img: Image.Image) -> float:
    hist = img.convert("L").histogram()
    return 1 - (hist[0] + hist[255]) / sum(hist)


def main() -> None:
    font_dir = sys.argv[1]
    svg = dense_svg()
    times, png = [], b""
    for _ in range(20):
        t = time.perf_counter()
        png = bytes(resvg_py.svg_to_bytes(svg_string=svg, font_dirs=[font_dir],
                                          skip_system_fonts=True))
        times.append((time.perf_counter() - t) * 1000)
    img = Image.open(io.BytesIO(png))
    one_bit = img.convert("L").convert("1", dither=Image.Dither.NONE)
    buf = io.BytesIO()
    one_bit.save(buf, format="PNG", optimize=True)
    print(f"resvg_py {resvg_py.__version__ if hasattr(resvg_py, '__version__') else ''}")
    print(f"median ms per frame: {statistics.median(times):.1f}")
    print(f"grey share before quantising: {grey_share(img):.4f}")
    print(f"1-bit PNG bytes: {len(buf.getvalue())}")
    if len(sys.argv) > 2:
        one_bit.save(sys.argv[2])


if __name__ == "__main__":
    main()
