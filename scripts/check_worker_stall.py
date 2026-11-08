"""B-088 check on a target host: main-thread stall with resvg in-process vs in the worker.

python -m scripts.check_worker_stall <svg file>
"""

import sys
import threading
import time
from pathlib import Path

from custom_components.paperboard.fonts import FONT_DIR
from custom_components.paperboard.raster_worker import RasterWorker, svg_to_png


def stall(render, svg: str, n: int = 10) -> tuple[float, float]:
    done = threading.Event()

    def work() -> None:
        for _ in range(n):
            render(svg, str(FONT_DIR))
        done.set()

    thread = threading.Thread(target=work)
    start = last = time.perf_counter()
    thread.start()
    longest = 0.0
    while not done.is_set():
        time.sleep(0.001)
        now = time.perf_counter()
        longest, last = max(longest, now - last), now
    thread.join()
    return (time.perf_counter() - start) / n * 1000, longest * 1000


if __name__ == "__main__":
    svg = Path(sys.argv[1]).read_text()
    worker = RasterWorker()
    t = time.perf_counter()
    worker.render(svg, str(FONT_DIR))
    print(f"worker spawn + first render {(time.perf_counter() - t) * 1000:.0f} ms")
    for label, fn in (("in-process", svg_to_png), ("worker", worker.render)):
        per, longest = stall(fn, svg)
        print(f"{label:10s} {per:6.0f} ms/render, longest main-thread stall {longest:6.0f} ms")
    worker.shutdown(wait=True)
