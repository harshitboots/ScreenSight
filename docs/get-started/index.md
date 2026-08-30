# Overview

ScreenSight gives a coding agent one narrow, auditable capability: take a screenshot of your
screen, right now, because you asked for it. Everything else in the project exists to make
that capability safe and to make it reachable from whichever agent you happen to use.

## Three surfaces, one core

| Surface | Module | Who it's for |
|---|---|---|
| **MCP server** | `mcp_server.py` | Any MCP-capable agent — Cursor, Windsurf, Cline, Claude Code, Codex CLI |
| **CLI** | `__main__.py` | Aider, raw shell agents, scripts, humans |
| **Watch daemon** | `watch.py` | Unattended interval capture, started and polled by the other two |

All three call the same function — `core.capture_once()` — which composes the switch check,
the blocklist check, redaction, downscaling and hashing in a fixed order. A surface cannot
opt out of a safety property, because a surface never touches a platform backend directly.

## What a capture actually does

1. Read the master switch at `~/.screensight/state.json`. If it's off, stop.
2. Ask the platform backend for a screenshot and the active window title.
3. Match the title against the sensitive-app blocklist. On a match, abort — nothing is written.
4. Black out any configured redaction zones.
5. Downscale to a 1568px long edge.
6. Hash the result with SHA-256 and write it to `~/.screensight/frame.jpg`.

The frame file is the whole storage model. There is no database, no history, no upload.

## Requirements

- Python 3.10 or newer
- One of the supported platforms:

| Platform | Status | Backend |
|----------|--------|---------|
| Windows | ✅ Tested | PowerShell + System.Drawing |
| macOS | ⚠️ Untested | `screencapture` + `osascript` |
| Linux | ⚠️ Untested | `grim` / `gnome-screenshot` / `import` + `xdotool` |
| WSL | ⚠️ Untested | PowerShell (captures the Windows desktop) |

Screenshots are taken with native OS tools via `subprocess`, never a Python screenshot
library — that keeps the "no extra app, no extra deps" property intact.

## Next

<div class="ss-grid" markdown>

<a class="ss-card" href="installation/">
<span class="ss-card__title">:material-download: Installation</span>
<span class="ss-card__body">Get the <code>screensight</code> and <code>screensight-mcp</code> binaries on your PATH.</span>
<span class="ss-card__meta">Install →</span>
</a>

<a class="ss-card" href="quickstart/">
<span class="ss-card__title">:material-rocket-launch: Quickstart</span>
<span class="ss-card__body">First capture in five commands.</span>
<span class="ss-card__meta">Start →</span>
</a>

</div>
