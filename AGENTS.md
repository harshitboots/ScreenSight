# AGENTS.md

Instructions for any coding agent (opencode, Claude Code, etc.) working in this repo.

## Read first

Read `PROJECT.md` fully before writing code. It defines what's already built, what's left, and the safety invariants that are not up for reinterpretation.

## Ground rules

1. **Never bypass `core.capture_once()`.** Every code path that ends in a screenshot — CLI, MCP tool, daemon loop — must call `core.capture_once()`. Do not call `capture/*.py` backends directly from anywhere except `core.py`. If a new surface needs capture, import from `core`, not from `capture`.
2. **The master switch check stays inside `core.py`.** Don't add a redundant "is it on?" check anywhere else that could drift out of sync — one source of truth.
3. **Don't weaken the blocklist or redaction silently.** If you need to change matching logic (e.g. blocklist substring → regex), keep it strictly more conservative (fewer false negatives), and note the change in `PROJECT.md`'s non-negotiables section if the behavior contract changes.
4. **No new screenshot files accumulate on disk.** One frame path (`config.FRAME_PATH`), overwritten. If you add a "keep last N frames for diffing" feature, store them under `~/.screensight/` with the same off/cleanup guarantees, and delete on `screensight off`.
5. **Cross-platform parity.** If you add a feature to one `capture/*.py` backend, add it (or a documented graceful fallback) to all three. `active_window_title()` returning `None` is a valid fallback — callers must already treat `None` as "unknown," never as "safe."
6. **No new runtime dependencies without a reason.** Current deps: `fastmcp`, `pillow`. CLI uses stdlib `argparse`, not `click` — keep it that way unless there's a concrete need. Platform capture uses native OS tools via `subprocess`, never a screenshot pip package (keeps the "no extra app" property from the original).
7. **Daemon must be a separate OS process, not a thread inside the MCP server.** MCP servers commonly run over stdio per-session; a daemon needs to outlive that. `watch.py` should be launchable via `subprocess.Popen(..., start_new_session=True)` from both the CLI and the MCP tool, writing its own pidfile (`config.DAEMON_PID_FILE`) so `screen_watch_stop` can find and kill it.
8. **MCP tool docstrings are user-facing.** The calling agent reads the docstring to decide when to invoke a tool — write it like a man page entry, not a code comment. Tools live in `src/screensight/tools/` split by domain (`control.py`, `screen.py`, `audio.py`, `watch.py`). Each module exports a `register(mcp: FastMCP) -> None` function; `mcp_server.py` is a thin orchestrator that calls `register_all(mcp)` from `tools/__init__.py`. To add a new tool, add the function to the appropriate domain module and register it there — do not add inline tools to `mcp_server.py`.

## Conventions

- Python 3.10+, type hints everywhere, `from __future__ import annotations` at the top of every module (already the pattern in existing files — match it).
- `dataclasses` for structured returns (see `CaptureResult`, `CaptureOutcome`) instead of raw dicts/tuples, except at JSON-serialization boundaries (state files).
- No print statements inside `src/screensight/*` library code except `__main__.py` (CLI output) — library functions return values, the CLI formats them.
- Errors surface as `ok: bool` + `error: str | None` on result dataclasses, not exceptions, for anything that can fail for an expected reason (tool missing, permission denied, switch off). Reserve exceptions for genuine bugs.

## Build order (see TASKS.md for the checklist)

Build in this order — each step is independently testable before the next depends on it:

1. `watch.py` (daemon) — testable via CLI alone before MCP exists.
2. `__main__.py` (CLI) — wire up `on/off/status/capture/watch/watch-stop/displays` against `core.py` and `watch.py`.
3. Manually verify end-to-end on whatever OS you're running in (screenshot appears, blocklist works, watch daemon writes status file, `off` cleans up).
4. `tools/` sub-package — one module per domain (`control.py`, `screen.py`, `audio.py`, `watch.py`), each exporting a `register(mcp)` function. `mcp_server.py` is a thin orchestrator that calls `register_all(mcp)`. If you're duplicating logic between CLI and MCP server, stop and extract it into `core.py` or `watch.py` instead.
5. `install.sh` / `install.ps1`.
6. `skills/claude-code/SKILL.md` adapter.
7. `README.md`.
8. `tests/`.

## Definition of done for v1

- `pip install .` works from a clean venv.
- `screensight on && screensight capture` produces a valid downscaled JPEG at `~/.screensight/frame.jpg` on macOS, Linux, and Windows/WSL (test whichever you have access to; note untested platforms in the PR description).
- `screensight watch --interval 3` runs as a background process, updates `daemon.json` on change, stops itself after `MAX_FRAMES_PER_WATCH` frames or on `screensight watch-stop`, and turns the master switch off when it exits.
- `screensight-mcp` starts and lists all 9 tools when queried via any MCP client (`fastmcp dev` or an actual agent).
- Renaming the active window to something in the blocklist (e.g. a terminal titled "1Password") causes `capture` to refuse and report why.
- `screensight off` deletes `frame.jpg` if present.

## FastMCP Official Documentation

Reference: [FastMCP llms.txt](https://gofastmcp.com/llms.txt) — the fast, Pythonic way to build MCP servers and clients.

### Core Server Concepts

- [The FastMCP Server](https://gofastmcp.com/servers/server.md): The core FastMCP server class for building MCP applications
- [Tools](https://gofastmcp.com/servers/tools.md): Expose functions as executable capabilities for your MCP client
- [Resources & Templates](https://gofastmcp.com/servers/resources.md): Expose data sources and dynamic content generators to your MCP client
- [Prompts](https://gofastmcp.com/servers/prompts.md): Create reusable, parameterized prompt templates for MCP clients
- [MCP Context](https://gofastmcp.com/servers/context.md): Access MCP capabilities like logging, progress, and resources within your MCP objects

### Server Features

- [Authentication](https://gofastmcp.com/servers/auth/authentication.md): Secure your FastMCP server with flexible authentication patterns
- [Middleware](https://gofastmcp.com/servers/middleware.md): Add cross-cutting functionality with middleware that intercepts and modifies requests and responses
- [Lifespans](https://gofastmcp.com/servers/lifespan.md): Server-level setup and teardown with composable lifespans
- [Session State](https://gofastmcp.com/servers/sessions.md): Persist state across requests on stateless connections
- [Sampling](https://gofastmcp.com/servers/sampling.md): Generate text from a FastMCP server — by calling an LLM directly, or by asking the client to sample
- [Progress Reporting](https://gofastmcp.com/servers/progress.md): Update clients on the progress of long-running operations
- [Client Logging](https://gofastmcp.com/servers/logging.md): Send log messages back to MCP clients through the context
- [Testing your FastMCP Server](https://gofastmcp.com/servers/testing.md): How to test your FastMCP server

### Transforms & Providers

- [Transforms Overview](https://gofastmcp.com/servers/transforms/transforms.md): Modify components as they flow through your server
- [Tool Transformation](https://gofastmcp.com/servers/transforms/tool-transformation.md): Modify tool schemas - rename, reshape arguments, and customize behavior
- [Providers](https://gofastmcp.com/servers/providers/overview.md): How FastMCP sources tools, resources, and prompts
- [MCP Proxy Provider](https://gofastmcp.com/servers/providers/proxy.md): Source components from other MCP servers

### CLI & Deployment

- [CLI](https://gofastmcp.com/cli/overview.md): The fastmcp command-line interface
- [Running Servers](https://gofastmcp.com/cli/running.md): Start, develop, and configure servers from the command line
- [HTTP Deployment](https://gofastmcp.com/deployment/http.md): Deploy your FastMCP server over HTTP for remote access
- [Project Configuration](https://gofastmcp.com/deployment/server-configuration.md): Use fastmcp.json for portable, declarative project configuration

### Client

- [The FastMCP Client](https://gofastmcp.com/clients/client.md): Programmatic client for interacting with MCP servers
- [Calling Tools](https://gofastmcp.com/clients/tools.md): Execute server-side tools and handle structured results
- [Client Transports](https://gofastmcp.com/clients/transports.md): Configure how clients connect to and communicate with MCP servers

### Installation & Upgrading

- [Installation](https://gofastmcp.com/getting-started/installation.md): Install FastMCP and verify your setup
- [Quickstart](https://gofastmcp.com/getting-started/quickstart.md)
- [Upgrading from FastMCP 2](https://gofastmcp.com/getting-started/upgrading/from-fastmcp-2.md): What changed in FastMCP 3
