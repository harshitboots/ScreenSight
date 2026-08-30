# Contributing to ScreenSight

Thanks for your interest in contributing! ScreenSight lets *any* coding agent
see your screen — as an MCP server, a plain CLI, or a watch daemon. It's a small,
focused Python codebase with strict privacy invariants, so contributions of any
size are welcome as long as they respect those invariants.

Before you start, read these three files — they define what already exists and
the rules that are **not** up for reinterpretation:

- [`PROJECT.md`](PROJECT.md) — what's built, what's out of scope, the six non-negotiables
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — data flow and why `core.capture_once()` is the choke point
- [`AGENTS.md`](AGENTS.md) — ground rules and coding conventions (applies to humans too)

## Ways to contribute

- **Test an untested platform.** macOS, Linux, and WSL backends are written but
  marked ⚠️ untested in the README. Running the test suite and a manual
  `screensight on && screensight capture` on one of those and reporting results
  is genuinely valuable.
- **Fix a bug** you hit while using it.
- **Improve a capture backend** (`src/screensight/capture/`) — better active-window
  detection, multi-monitor handling, new fallback tools.
- **Extend the privacy layer** (`src/screensight/privacy.py`) — as long as changes
  are strictly *more* conservative (see rule 3 below).
- **Improve docs** — the README, `GUIDE.md`, or per-agent MCP config examples in `examples/`.

If your change is large or changes a safety contract, open an issue first so we
can agree on the approach before you write code.

## Development setup

Requires **Python 3.10+**.

```bash
git clone git@github.com:himanshu231204/ScreenSight.git screensight
cd screensight

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.\.venv\Scripts\Activate.ps1     # Windows

pip install -e .
pip install pytest
```

Verify the two entry points work:

```bash
screensight --help
screensight-mcp --help    # starts the FastMCP server on stdio
```

## Running tests

```bash
pytest tests/ -v
```

Tests **never take a real screenshot** — capture backends are mocked and image
processing runs against `PIL`-generated fixtures (see
[`tests/test_privacy.py`](tests/test_privacy.py) and
[`tests/test_core.py`](tests/test_core.py)). Keep it that way: **do not add a test
that shells out to a real OS screenshot tool** — CI has no display.

When you add behavior, add a test for it. The existing suite covers:

| File | Covers |
|------|--------|
| `tests/test_state.py` | master switch on/off round-trip |
| `tests/test_privacy.py` | blocklist matching + redact-zone coordinate scaling |
| `tests/test_diff.py` | SHA-256 hashing and change detection |
| `tests/test_core.py` | `capture_once()` with a mocked backend |

## The six invariants (do not break these)

Every change must preserve the privacy guarantees from `PROJECT.md`:

1. **Off by default.** The master switch check lives inside `core.capture_once()`
   — never add a second, drift-prone check elsewhere.
2. **Never bypass `core.capture_once()`.** CLI, MCP tools, and the daemon must all
   route through it. Do not call `capture/*.py` backends directly from anywhere
   except `core.py`.
3. **Don't weaken the blocklist or redaction silently.** Changes to matching logic
   must be strictly *more* conservative (fewer false negatives). Note any behavior-
   contract change in `PROJECT.md`.
4. **No screenshot files accumulate on disk.** One frame path, overwritten, deleted
   on `screensight off`.
5. **Cross-platform parity.** A feature added to one `capture/*.py` backend must be
   added (or given a documented graceful fallback) to all three.
6. **No new runtime dependencies without a concrete reason.** Current runtime deps
   are `fastmcp` and `pillow`. The CLI uses stdlib `argparse`, not `click`.

## Coding conventions

Match the existing code (see `AGENTS.md` → Conventions):

- Python 3.10+, type hints everywhere, `from __future__ import annotations` at the
  top of every module.
- `dataclasses` for structured returns (e.g. `CaptureResult`, `CaptureOutcome`),
  except at JSON-serialization boundaries (state files).
- No `print` inside `src/screensight/*` except `__main__.py` — library functions
  return values; the CLI formats them.
- Expected failures surface as `ok: bool` + `error: str | None` on result
  dataclasses, not exceptions. Reserve exceptions for genuine bugs.
- MCP tool docstrings are user-facing — write them like a man-page entry, since
  the calling agent reads them to decide when to invoke the tool.

## Submitting a pull request

1. Fork the repo and create a branch from `main`.
2. Make your change, add/update tests, and run `pytest tests/ -v`.
3. If you touched a capture backend, note in the PR **which platform you actually
   tested on** and which you didn't — untested is fine, undisclosed is not.
4. Open the PR against `main` and fill out the template.

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
