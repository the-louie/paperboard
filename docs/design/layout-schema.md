# Layout schema

## Validation library (Sprint 02 T-01, 2026-11-08)

**Decision:** layouts are validated with the `schema.py` shim. It uses **probatio** where HA
ships it (all 884 core config flows use it by 2026.11) and falls back to **voluptuous** on
older cores within our minimum (`hacs.json`: 2026.3.0).

- **Same API subset:** `Schema`, `Required`, `Optional`, `In`, `Range`, `All`, `Any`,
  `Coerce`.
- **Error paths:** both libraries carry `.path`. probatio reports **every** error in a file,
  voluptuous only the first. `schema.format_errors()` turns them into
  `widgets[1].area: expected str`. These strings go into the Repairs issue (B-029), so a
  layout author sees all problems at once on modern cores.
- **Rejected:**
  - plain dataclasses with hand-written checks: more code, worse messages;
  - pydantic: not a core dependency, and a pin would conflict with other integrations.
