# Testing

## Harness (T-02, 2026-11-08)

- **Package:** `pytest-homeassistant==2026.11.0`, on PyPI, `requires_python >=3.14.2`. It pins
  `homeassistant==2026.11.0`; upgrade the two together.
- **The old package:** `pytest-homeassistant-custom-component` is *not* used. Its successor's
  README says not to install both, because their fixtures overlap.
- **Install:** `uv venv -p 3.14 .venv && uv pip install -p .venv/bin/python
  pytest-homeassistant==2026.11.0 resvg-py ruff`. This takes about 12 s with a warm uv cache.
- **Configuration** in `pyproject.toml`, as the package README requires:
  - `asyncio_mode = "auto"`;
  - `asyncio_default_fixture_loop_scope = "function"`;
  - `addopts = "-p no:respx"`, so HA installs its httpx alias before respx is imported;
  - `pythonpath = ["."]`.
- **Fixtures** come from `pytest_homeassistant.plugins`, loaded automatically through the
  `pytest11` entry point: `hass`, `hass_client`, `hass_client_no_auth`, `aioclient_mock`,
  `freezer`, registry fixtures and `snapshot` (syrupy 6.1.1).
  - Custom integrations are enabled by default, so `enable_custom_integrations` is not needed.
  - Import helpers from `pytest_homeassistant.common` (`MockConfigEntry`, `load_fixture`,
    `async_fire_time_changed`).
- **Fixture files:** `load_fixture` reads `tests/fixtures/`.

## Fallback

None needed: the package exists and runs on the venv's CPython 3.14.6. If it ever lags behind
an HA release, pin both `homeassistant` and `pytest-homeassistant` to the last matching pair.

## Commands

```
.venv/bin/ruff check .
.venv/bin/pytest -q
```

## Golden images (T-11)

- **Helper:** `tests/golden_util.assert_golden(name, png)` compares against
  `tests/golden/<name>.png` and requires an **exact** pixel match.
  - On mismatch it writes `tests/output/<name>.actual.png` and `<name>.diff.png` (changed
    pixels black) and fails with the pixel count.
  - `tests/output/` is git-ignored.
- **Creating and updating:**
  - A missing golden is created on first run locally. In CI (`CI` set), a missing golden
    fails.
  - Re-render all goldens with `python scripts/update_golden.py`, then review the PNGs in the
    diff before committing.
- **Determinism:**
  - Fonts come only from the bundled dir (`skip_system_fonts`).
  - Rendering code receives `now` as a parameter (never `datetime.now()` inside a widget), so
    a golden is frozen by passing a fixed time.
  - State fixtures live in `tests/fixtures/states/*.json` (T-12).
