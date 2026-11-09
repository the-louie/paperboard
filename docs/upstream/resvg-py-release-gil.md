# Draft issue for resvg-py: release the GIL while rendering

**For:** https://github.com/baseplate-admin/resvg-py/issues (new issue). The owner posts it.
**Drafted:** 2026-11-09 (paperboard B-090). Checked against `master`: `svg_to_bytes` does not
call `py.allow_threads` / `py.detach`; the module only declares `#[pymodule(gil_used = false)]`.

---

**Title:** `svg_to_bytes` holds the GIL for the whole render; could it release it?

**Body:**

Thanks for resvg-py. It is the only way we found to get resvg into a Home Assistant
integration without system libraries.

`svg_to_bytes` keeps the GIL for the entire parse + render. In an asyncio application that
calls it from a worker thread (`loop.run_in_executor`), the event loop therefore cannot run
until the render finishes, even though the work is pure Rust and never touches Python
objects.

**Measured** (resvg-py 0.5.0, an 800×480 SVG with ~20 text runs):

| Host | Main-thread longest stall per render: render in a thread | Render in a separate process |
|---|---|---|
| Intel i5, 4 cores, normal clock | 63 ms (render 32 ms) | 2 ms |
| Same CPU, VM clocked at 792 MHz | 560 ms (up to 5.1 s in the real app) | 22 ms |

The "separate process" column is our workaround: a long-lived child process that runs only
resvg-py. It works, but it adds a process, a pipe protocol, and shutdown handling to get
around what is a one-line change in the binding.

**Suggestion:** take `py: Python<'_>` in `svg_to_bytes` and run the parse/render inside
`py.allow_threads(|| ...)` (pyo3 < 0.26) or `py.detach(|| ...)` (pyo3 ≥ 0.26). Convert
the input strings to owned Rust values first, and build the `PyErr` after the closure returns.
Everything between "SVG string in" and "PNG bytes out" is plain Rust (`usvg` + `resvg` +
`tiny-skia`), so nothing inside needs the GIL.

A small reproducer: a thread that calls `svg_to_bytes` in a loop, and a main thread that sleeps
1 ms in a loop and records the largest gap between wake-ups. Today the largest gap is about the
render time; with the GIL released it should be about 1 ms.

Happy to test a pre-release wheel.
