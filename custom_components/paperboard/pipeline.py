"""SVG -> panel PNG. Pure functions, no Home Assistant objects: runs in an executor job.

Steps: resvg (crisp flags forced on the root) -> Pillow 'L' -> exact 2- or 4-level palette
with NO dithering -> hand-written grayscale PNG (1 or 2 bit) -> byte-limit check.
The PNG encoder is ported from the owner's trmnl-service (MIT,
<the maintainer's earlier TRMNL server>).
"""

from __future__ import annotations

import hashlib
import io
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

import resvg_py
from PIL import Image

CRISP_ATTRS = 'shape-rendering="crispEdges" text-rendering="optimizeSpeed"'
GRAY4 = (0, 85, 170, 255)


class PipelineError(Exception):
    """The frame could not be produced; callers keep serving the last good image."""


class ImageTooLargeError(PipelineError):
    """Encoded PNG exceeds the panel's download limit."""


@dataclass(frozen=True)
class PanelProfile:
    """What the panel accepts."""

    width: int = 800
    height: int = 480
    bit_depth: int = 1  # 1 or 2
    byte_limit: int = 90_000  # TRMNL OG without PSRAM


@dataclass(frozen=True)
class Frame:
    png: bytes
    sha: str  # first 16 hex chars of sha256; used as the device-visible filename


def _ensure_crisp(svg: str) -> str:
    head, sep, rest = svg.partition("<svg")
    if not sep:
        raise PipelineError("not an SVG document")
    tag_end = rest.index(">")
    tag = rest[:tag_end]
    if "shape-rendering" not in tag:
        tag += " " + CRISP_ATTRS
    return head + sep + tag + rest[tag_end:]


def rasterize(svg: str, profile: PanelProfile, font_dir: Path) -> Image.Image:
    """resvg -> 8-bit grayscale image of exactly the panel size."""
    try:
        data = bytes(resvg_py.svg_to_bytes(svg_string=_ensure_crisp(svg),
                                           font_dirs=[str(font_dir)], skip_system_fonts=True))
    except Exception as err:  # resvg raises plain exceptions on parse errors
        raise PipelineError(f"resvg failed: {err}") from err
    img = Image.open(io.BytesIO(data))
    img.load()
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGBA", img.size, "white")
        img = Image.alpha_composite(background, img.convert("RGBA"))
    gray = img.convert("L")
    if gray.size != (profile.width, profile.height):
        raise PipelineError(f"SVG renders {gray.size}, panel is {profile.width}x{profile.height}")
    return gray


def _chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def encode_png_gray(rows: list[bytes], width: int, height: int, bit_depth: int) -> bytes:
    """Grayscale PNG (colour type 0) at bit depth 1 or 2; filter 0 on every scanline."""
    raw = b"".join(b"\x00" + row for row in rows)
    ihdr = struct.pack(">IIBBBBB", width, height, bit_depth, 0, 0, 0, 0)
    return b"".join([b"\x89PNG\r\n\x1a\n", _chunk(b"IHDR", ihdr),
                     _chunk(b"IDAT", zlib.compress(raw, 9)), _chunk(b"IEND", b"")])


def quantize_1bit(gray: Image.Image) -> list[bytes]:
    """Threshold at 128 (no dither) -> packed rows, 1 = white."""
    bw = gray.point(lambda v: 255 if v >= 128 else 0).convert("1", dither=Image.Dither.NONE)
    row_bytes = (bw.width + 7) // 8
    packed = bw.tobytes()
    return [packed[y * row_bytes : (y + 1) * row_bytes] for y in range(bw.height)]


def quantize_2bit(gray: Image.Image) -> list[bytes]:
    """Nearest of 4 grey levels (no dither) -> packed rows, 0 = black, 3 = white."""
    idx = gray.point(lambda v: min(3, (v + 42) // 85)).tobytes()
    width = gray.width
    pad = (-width) % 4
    rows = []
    for y in range(gray.height):
        line = idx[y * width : (y + 1) * width] + b"\x03" * pad
        rows.append(bytes(a << 6 | b << 4 | c << 2 | d
                          for a, b, c, d in zip(line[0::4], line[1::4], line[2::4], line[3::4],
                                                strict=True)))
    return rows


def encode_bmp_1bit(png: bytes) -> bytes:
    """Any frame PNG -> 1-bpp BMP3 for firmware that only takes BMP (the setup image).

    Ported from the owner's trmnl-service: pixel offset 62, palette 0 = black, 1 = white,
    bottom-up rows padded to 4 bytes; 800x480 gives exactly 48 062 bytes.
    """
    img = Image.open(io.BytesIO(png))
    img.load()
    bw = img.convert("L").point(lambda v: 255 if v >= 128 else 0).convert(
        "1", dither=Image.Dither.NONE)
    width, height = bw.size
    row_bytes = (width + 7) // 8
    stride = (row_bytes + 3) & ~3
    packed = bw.tobytes()
    rows = [packed[y * row_bytes : (y + 1) * row_bytes].ljust(stride, b"\x00")
            for y in range(height)]
    pixels = b"".join(reversed(rows))
    palette = bytes([0, 0, 0, 0, 255, 255, 255, 0])
    offset = 14 + 40 + len(palette)
    file_header = struct.pack("<2sIHHI", b"BM", offset + len(pixels), 0, 0, offset)
    info_header = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 1, 0, len(pixels),
                              2835, 2835, 2, 2)
    return file_header + info_header + palette + pixels


def render(svg: str, profile: PanelProfile, font_dir: Path) -> Frame:
    """The whole pipeline. Raises PipelineError; never returns a partial frame."""
    gray = rasterize(svg, profile, font_dir)
    if profile.bit_depth == 1:
        rows = quantize_1bit(gray)
    elif profile.bit_depth == 2:
        rows = quantize_2bit(gray)
    else:
        raise PipelineError(f"unsupported bit depth {profile.bit_depth}")
    png = encode_png_gray(rows, profile.width, profile.height, profile.bit_depth)
    if len(png) > profile.byte_limit:
        raise ImageTooLargeError(f"{len(png)} bytes > limit {profile.byte_limit}")
    return Frame(png=png, sha=hashlib.sha256(png).hexdigest()[:16])
