"""Schema library shim.

HA core moved its own flows and services from voluptuous to probatio (a voluptuous-compatible
fork) by 2026.11. paperboard supports HA >= 2026.3, so it uses probatio when present and
falls back to voluptuous on older cores. Only the shared API subset is used.
"""

try:
    import probatio as vol
except ImportError:  # HA before the probatio migration
    import voluptuous as vol  # type: ignore[no-redef]



def format_errors(err: Exception) -> list[str]:
    """Readable error paths for a layout file: 'widgets[1].area: expected str'.

    probatio reports every error, voluptuous only the first; both carry .path.
    """
    errors = getattr(err, "errors", None) or [err]
    out = []
    for e in errors:
        path = ""
        for part in getattr(e, "path", []) or []:
            path += f"[{part}]" if isinstance(part, int) else (f".{part}" if path else str(part))
        msg = str(getattr(e, "msg", e))
        out.append(f"{path}: {msg}" if path else msg)
    return out


__all__ = ["format_errors", "vol"]
