"""T-07 spike: does Pillow measure text the way resvg draws it?

For each font/size, derive resvg's advance width from the ink shift between a start-anchored
and an end-anchored copy of the same string, and compare it with Pillow's getlength(). Also
compare ink widths (resvg pixels vs Pillow getbbox).
"""

import io

import resvg_py
from PIL import Image

from custom_components.paperboard.fonts import FONT_DIR, load_fonts

SAMPLES = ["Kök 20,9°", "Söndag 8 november", "0,5 (1,5) m/s SO", "1,89 kr/kWh", "−0,8°"]
CASES = [("TRMNL12", 400, 12), ("TRMNL12", 700, 12), ("TRMNL16", 400, 16), ("TRMNL16", 700, 16),
         ("TRMNL21", 400, 21), ("TRMNL21", 700, 21), ("Inter", 500, 26), ("Inter", 700, 38),
         ("Inter", 700, 58), ("Inter", 800, 74)]


def ink(svg: str) -> tuple[int, int]:
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, font_dirs=[str(FONT_DIR)],
                                      skip_system_fonts=True))
    img = Image.open(io.BytesIO(png)).convert("L").point(lambda v: 255 if v < 128 else 0)
    box = img.getbbox()
    assert box, svg
    return box[0], box[2]


def svg_for(family: str, weight: int, size: int, text: str, anchor: str, x: int) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="120" '
            'text-rendering="optimizeSpeed"><rect width="1400" height="120" fill="#fff"/>'
            f'<text x="{x}" y="90" font-family="{family}" font-weight="{weight}" '
            f'font-size="{size}" text-anchor="{anchor}">{text}</text></svg>')


def main() -> None:
    reg = load_fonts()
    worst_adv = worst_ink = 0.0
    print(f"{'font':14} {'size':>4} {'max |Δadvance| px':>18} {'max |Δink| px':>14}")
    for family, weight, size in CASES:
        font = reg.pillow(family, weight, size)
        d_adv = d_ink = 0.0
        for text in SAMPLES:
            l1, r1 = ink(svg_for(family, weight, size, text, "start", 10))
            l2, _ = ink(svg_for(family, weight, size, text, "end", 1390))
            adv_resvg = 1380 - (l2 - l1)
            bb = font.getbbox(text)
            d_adv = max(d_adv, abs(adv_resvg - font.getlength(text)))
            d_ink = max(d_ink, abs((r1 - l1) - (bb[2] - bb[0])))
        worst_adv, worst_ink = max(worst_adv, d_adv), max(worst_ink, d_ink)
        print(f"{family}-{weight:<6} {size:>4} {d_adv:>18.1f} {d_ink:>14.1f}")
    print(f"worst: advance {worst_adv:.1f} px, ink {worst_ink:.1f} px")


if __name__ == "__main__":
    main()
