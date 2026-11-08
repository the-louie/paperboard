"""B-088: resvg runs in a worker process and the calling thread does not hold the GIL."""

import threading
import time

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.raster_worker import RasterWorker, svg_to_png

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
