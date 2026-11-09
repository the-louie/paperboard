"""B-088: resvg runs in a worker process and the calling thread does not hold the GIL."""

import threading
import time

import pytest

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.raster_worker import RasterWorker, RenderError, svg_to_png

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="480">'
       '<rect width="800" height="480" fill="#fff"/>'
       + "".join(f'<text x="10" y="{20 + i * 20}" font-family="Inter" font-size="18">'
                 f'Rad {i} 12,3°</text>' for i in range(20)) + "</svg>")


def test_worker_matches_in_process() -> None:
    worker = RasterWorker()
    try:
        assert worker.render(SVG, str(FONT_DIR)) == svg_to_png(SVG, str(FONT_DIR))
    finally:
        worker.shutdown(wait=True)


def test_main_thread_keeps_running_while_the_worker_renders() -> None:
    worker = RasterWorker()
    try:
        worker.render(SVG, str(FONT_DIR))  # spawn outside the measurement
        done = threading.Event()

        def work() -> None:
            for _ in range(20):
                worker.render(SVG, str(FONT_DIR))
            done.set()

        thread = threading.Thread(target=work)
        started = time.perf_counter()
        thread.start()
        longest, last = 0.0, time.perf_counter()
        while not done.is_set():
            time.sleep(0.001)
            now = time.perf_counter()
            longest, last = max(longest, now - last), now
        thread.join()
        # In-process, the main thread stalls for a whole render; here only for IPC.
        assert longest < 0.05, f"main thread stalled {longest * 1000:.0f} ms"
        assert time.perf_counter() - started < 30
    finally:
        worker.shutdown(wait=True)


def test_worker_restarts_after_shutdown() -> None:
    worker = RasterWorker()
    try:
        first = worker.render(SVG, str(FONT_DIR))
        worker.shutdown(wait=True)
        assert worker.render(SVG, str(FONT_DIR)) == first
    finally:
        worker.shutdown(wait=True)


def test_worker_starts_no_threads() -> None:
    """B-092: ProcessPoolExecutor's non-daemonic threads hung HA's exit. This worker has none."""
    before = {t.ident for t in threading.enumerate()}
    worker = RasterWorker()
    try:
        worker.render(SVG, str(FONT_DIR))
        new = [t for t in threading.enumerate() if t.ident not in before]
        assert new == [], f"worker started threads: {new}"
    finally:
        worker.shutdown(wait=True)


def test_shutdown_ends_the_child() -> None:
    worker = RasterWorker()
    worker.render(SVG, str(FONT_DIR))
    proc = worker._proc
    assert proc is not None and proc.poll() is None
    worker.shutdown(wait=True)
    assert proc.poll() is not None


def test_bad_svg_raises_and_the_worker_survives() -> None:
    worker = RasterWorker()
    try:
        with pytest.raises(RenderError):
            worker.render("<svg", str(FONT_DIR))
        assert worker.render(SVG, str(FONT_DIR)) == svg_to_png(SVG, str(FONT_DIR))
    finally:
        worker.shutdown(wait=True)


def test_a_killed_child_is_replaced() -> None:
    worker = RasterWorker()
    try:
        worker.render(SVG, str(FONT_DIR))
        worker._proc.kill()
        worker._proc.wait()
        # The dead child is noticed before the write and a new one serves the render.
        assert worker.render(SVG, str(FONT_DIR)) == svg_to_png(SVG, str(FONT_DIR))
    finally:
        worker.shutdown(wait=True)


def test_child_exits_when_the_parent_goes_away() -> None:
    """EOF on stdin ends the child, so it never outlives a killed Home Assistant."""
    worker = RasterWorker()
    worker.render(SVG, str(FONT_DIR))
    proc = worker._proc
    proc.stdin.close()  # what the kernel does when the parent dies
    assert proc.wait(timeout=5) == 0
    worker._proc = None
