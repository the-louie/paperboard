"""Schema library shim.

HA core moved its own flows and services from voluptuous to probatio (a voluptuous-compatible
fork) by 2026.11. paperboard supports HA >= 2026.3, so it uses probatio when present and
falls back to voluptuous on older cores. Only the shared API subset is used.
"""

try:
    import probatio as vol
except ImportError:  # HA before the probatio migration
    import voluptuous as vol  # type: ignore[no-redef]

__all__ = ["vol"]
