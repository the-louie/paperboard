"""resvg in a separate process (B-088), without threads that block HA's exit (B-092).

resvg-py 0.5.0 holds the GIL for the whole render (measured 2026-11-08: a main thread got one
tick per render). Run in HA's executor, every render therefore froze the event loop: 0.3-5 s on
ha-host. A single persistent child process renders instead; the executor thread that waits
for it blocks in a pipe read, which releases the GIL, so the loop keeps running.

B-092: the first version used concurrent.futures.ProcessPoolExecutor. Its management thread
is non-daemonic and joined at interpreter exit, so after the 2026.11 upgrade HA's restart hung
on "Found 3 non-daemonic threads" for ~10 min. This version starts NO threads: a plain
subprocess.Popen with length-prefixed messages on stdin/stdout. The child exits on EOF, so it
also dies with HA if HA is killed. HA's stop event and unload both call shutdown().

The child imports only resvg_py (not this package, which would import Home Assistant: 8.3 s).
"""

from __future__ import annotations

import json
import logging
import os
import select
import struct
import subprocess
import sys
import threading
from pathlib import Path

import resvg_py

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 60  # seconds per render; resvg on the slowest host measured 5 s
_HEADER = struct.Struct(">BI")  # status (0 ok, 1 error), payload length

# Runs in the child. Request: 4-byte length + JSON {"svg", "font_dir"}. Reply: _HEADER + body.
_CHILD = r"""
import json, struct, sys
sys.path.insert(0, sys.argv[1])
import resvg_py
inp, out = sys.stdin.buffer, sys.stdout.buffer
while True:
    head = inp.read(4)
    if len(head) < 4:
        break  # EOF: the parent closed the pipe or died
    req = json.loads(inp.read(struct.unpack(">I", head)[0]))
    try:
        body, status = bytes(resvg_py.svg_to_bytes(
            svg_string=req["svg"], font_dirs=[req["font_dir"]], skip_system_fonts=True)), 0
    except Exception as err:  # noqa: BLE001 - reported to the parent
        body, status = repr(err).encode(), 1
    out.write(struct.pack(">BI", status, len(body)) + body)
    out.flush()
"""


def svg_to_png(svg: str, font_dir: str) -> bytes:
    """In-process render (tests, and the fallback)."""
    return bytes(resvg_py.svg_to_bytes(svg_string=svg, font_dirs=[font_dir],
                                       skip_system_fonts=True))


class RenderError(RuntimeError):
    """resvg raised in the child."""


class RasterWorker:
    """One child process, started on first use; falls back to in-process if it cannot."""

    def __init__(self) -> None:
        self._proc: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._disabled = False

    def render(self, svg: str, font_dir: str) -> bytes:
        """Blocking; call from an executor thread, never from the event loop."""
        if self._disabled:
            return svg_to_png(svg, font_dir)
        with self._lock:
            try:
                proc = self._get_proc()
            except OSError as err:  # no processes allowed here
                _LOGGER.warning("Cannot start a render process (%s); rendering in-process, "
                                "which blocks Home Assistant briefly per frame", err)
                self._disabled = True
                return svg_to_png(svg, font_dir)
            try:
                return self._roundtrip(proc, svg, font_dir)
            except RenderError:
                raise
            except (OSError, TimeoutError, ValueError):
                # Dead, hung or out of step: kill it; the next render starts a fresh one.
                self._kill()
                raise

    def _get_proc(self) -> subprocess.Popen[bytes]:
        if self._proc is None or self._proc.poll() is not None:
            site = str(Path(resvg_py.__file__).resolve().parent.parent)
            self._proc = subprocess.Popen(
                [sys.executable, "-c", _CHILD, site],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                close_fds=True, start_new_session=True)
        return self._proc

    @staticmethod
    def _roundtrip(proc: subprocess.Popen[bytes], svg: str, font_dir: str) -> bytes:
        assert proc.stdin is not None and proc.stdout is not None
        req = json.dumps({"svg": svg, "font_dir": font_dir}).encode()
        proc.stdin.write(struct.pack(">I", len(req)) + req)
        proc.stdin.flush()
        status, length = _HEADER.unpack(_read(proc.stdout, _HEADER.size))
        body = _read(proc.stdout, length)
        if status:
            raise RenderError(body.decode(errors="replace"))
        return body

    def _kill(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)

    def shutdown(self, wait: bool = False) -> None:
        """Stop the child. Closing stdin lets it exit on its own; kill it if it does not."""
        with self._lock:
            proc, self._proc = self._proc, None
        if proc is None:
            return
        try:
            if proc.stdin is not None:
                proc.stdin.close()
            proc.wait(timeout=5 if wait else 0.5)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait(timeout=5)
        finally:
            if proc.stdout is not None:
                proc.stdout.close()


def _read(stream, n: int) -> bytes:
    """Exactly n bytes, or OSError on EOF, or TimeoutError after TIMEOUT s of silence."""
    buf = bytearray()
    fd = stream.fileno()
    while len(buf) < n:
        ready, _, _ = select.select([fd], [], [], TIMEOUT)
        if not ready:
            raise TimeoutError(f"render process silent for {TIMEOUT} s")
        chunk = os.read(fd, n - len(buf))
        if not chunk:
            raise OSError("render process exited")
        buf += chunk
    return bytes(buf)


WORKER = RasterWorker()
