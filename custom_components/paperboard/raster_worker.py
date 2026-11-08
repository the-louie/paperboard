"""resvg in a separate process (B-088).

resvg-py 0.5.0 holds the GIL for the whole render (measured 2026-11-08: a main thread got one
tick per render). Run in HA's executor, every render therefore froze the event loop: 0.3-5 s on
ha-host. A single persistent worker process renders instead; the executor thread that waits
for it releases the GIL, so the loop keeps running.

The worker is handed `resvg_py.svg_to_bytes` itself, so the spawned process imports only
resvg_py. Handing it a function from this package made it import the package's __init__ and
Home Assistant with it: 8.3 s to start on ha-host.
"""

from __future__ import annotations

import logging
import multiprocessing
import threading
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

import resvg_py

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 60  # seconds per render; resvg on the slowest host measured 5 s


def _kwargs(svg: str, font_dir: str) -> dict:
    return {"svg_string": svg, "font_dirs": [font_dir], "skip_system_fonts": True}


def svg_to_png(svg: str, font_dir: str) -> bytes:
    """In-process render (tests, and the fallback)."""
    return bytes(resvg_py.svg_to_bytes(**_kwargs(svg, font_dir)))


class RasterWorker:
    """One worker process, started on first use; falls back to in-process if it cannot."""

    def __init__(self) -> None:
        self._pool: ProcessPoolExecutor | None = None
        self._lock = threading.Lock()
        self._disabled = False

    def render(self, svg: str, font_dir: str) -> bytes:
        """Blocking; call from an executor thread, never from the event loop."""
        if self._disabled:
            return svg_to_png(svg, font_dir)
        try:
            future = self._get_pool().submit(resvg_py.svg_to_bytes, **_kwargs(svg, font_dir))
            return bytes(future.result(timeout=TIMEOUT))
        except BrokenProcessPool:
            # The worker died (OOM killer, crash): start a fresh one next time.
            self.shutdown()
            raise
        except (OSError, RuntimeError) as err:  # no processes allowed here
            _LOGGER.warning("Cannot start a render process (%s); rendering in-process, "
                            "which blocks Home Assistant briefly per frame", err)
            self._disabled = True
            return svg_to_png(svg, font_dir)

    def _get_pool(self) -> ProcessPoolExecutor:
        with self._lock:
            if self._pool is None:
                # spawn, never fork: forking HA's threaded process can deadlock the child.
                self._pool = ProcessPoolExecutor(
                    max_workers=1, mp_context=multiprocessing.get_context("spawn"))
            return self._pool

    def shutdown(self, wait: bool = False) -> None:
        with self._lock:
            pool, self._pool = self._pool, None
        if pool is not None:
            pool.shutdown(wait=wait, cancel_futures=True)


WORKER = RasterWorker()
