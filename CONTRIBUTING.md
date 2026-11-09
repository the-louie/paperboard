# Contributing to Paperboard

**Contributions are welcome**: bug reports, layouts, widgets, translations, documentation and
code. Thank you for taking the time.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to help

- **Report a bug:** [open an issue](https://github.com/the-louie/paperboard/issues/new/choose)
  with the bug template. Attach the integration's diagnostics (Settings → Devices & services →
  Paperboard → ⋮ → Download diagnostics): they contain no secrets.
- **Suggest a feature:** open an issue with the feature template. Describe the problem first,
  then the solution you have in mind.
- **Share a layout:** a layout is one YAML file
  ([format](docs/design/layout-schema.md)). Open a pull request that adds it to
  `custom_components/paperboard/layouts_yaml/` together with a golden image (see below).
- **Translate:** copy `custom_components/paperboard/translations/en.json` to your language
  code (e.g. `de.json`) and translate the values, not the keys.
- **Security issues:** do **not** open a public issue; see [SECURITY.md](SECURITY.md).

## AI-assisted contributions

You may use AI tools (code assistants, chat models) to help write a contribution. If you do:
- **Say so** in the pull request description: which tool, and roughly what it produced.
- **You are the author.** You must understand every line you submit and be able to explain it
  in review. "The AI wrote it" isn't an answer to a review question.
- **Same bar as everything else:** tests, golden images you have actually looked at, and the
  empty-house rule. Generated code without tests won't be merged.
- **Licensing is your responsibility:** don't submit generated code you have reason to believe
  copies someone else's licensed work.
- **No unreviewed bulk changes.** Large AI-made rewrites or reformatting that nobody asked for
  will be closed.
- **Issues and reviews too:** don't post AI-generated bug reports or review comments you
  haven't verified yourself.

## Development setup

Paperboard targets Python 3.14 and Home Assistant 2026.3 or newer.

```bash
git clone https://github.com/the-louie/paperboard.git
cd paperboard
uv venv -p 3.14 .venv          # or: python3.14 -m venv .venv
uv pip install -p .venv/bin/python -r requirements_test.txt
.venv/bin/pytest -q            # the whole suite runs in about 15 s
.venv/bin/ruff check .
```

To try it in a real Home Assistant, copy `custom_components/paperboard` into your
configuration's `custom_components/` folder and restart Home Assistant.
`scripts/fake_trmnl.py` emulates a TRMNL device against a running instance.

## What a pull request needs

1. **Tests.** New behaviour comes with a test; a bug fix comes with a test that fails without
   the fix. The suite drives the real integration through `pytest-homeassistant`.
2. **Golden images for anything visible.** Rendering is checked pixel by pixel against
   `tests/golden/*.png`. When you change how something looks on purpose, regenerate only
   the goldens you meant to change:
   ```bash
   PAPERBOARD_UPDATE_GOLDEN=1 .venv/bin/pytest -q tests/test_<your_test>.py
   ```
   Look at the new PNGs before committing them. CI never creates goldens: a missing one
   fails.
3. **The empty-house rule.** No sensor is ever required. Every widget and every bundled
   layout is rendered against a home with **zero** entities and against garbage data
   (`tests/test_empty_house.py`). A new widget must collapse or show "—", never crash.
4. **Home Assistant rules.** No blocking I/O on the event loop (use
   `hass.async_add_executor_job`); no new runtime dependency without a wheel for both
   x86-64 and aarch64 (musl and glibc).
5. **Lint clean:** `ruff check .` passes.
6. **Docs.** User-visible changes update the README or `docs/`, and get a line under
   "Unreleased" in [CHANGELOG.md](CHANGELOG.md). New strings go in `strings.json` **and**
   every file in `translations/`.

CI runs the lint, the tests on x86-64 and aarch64, `hassfest` and the HACS validation on every
pull request.

## How the code is organised

| Path | What |
|---|---|
| `custom_components/paperboard/__init__.py` | setup: hub, screens, renderers |
| `config_flow.py` | the hub, roles and screen forms |
| `views.py` | the TRMNL device API (`/api/setup`, `/api/display`, `/api/log`) and image URLs |
| `renderer.py`, `compose.py`, `pipeline.py` | snapshot → SVG → resvg → panel PNG |
| `widgets*.py`, `widget_registry.py` | the widgets layouts are built from |
| `layouts_yaml/` | the bundled layouts |
| `docs/design/` | design documents: start with [rendering](docs/design/rendering.md) |

`docs/planning/` and `docs/research/` hold the project's own planning notes; you don't need
them to contribute.

## Commit messages

Use a short summary line (what changed, in the imperative), a blank line, then why. Reference
the issue you fix (`Fixes #12`).

## Licence

Paperboard is licensed under the [Apache License 2.0](LICENSE). By contributing you agree that
your contribution is licensed under the same terms (Apache-2.0, section 5).
