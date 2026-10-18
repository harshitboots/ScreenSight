# Changelog

All notable changes to ScreenSight are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **System-audio capture** ([#4](https://github.com/himanshu231204/ScreenSight/issues/4)) —
  record the system's audio output (loopback) as a WAV:
  - New `screen_capture_audio` MCP tool (9 tools total) returning the recording as an
    audio content block.
  - New `screensight capture-audio [--duration N]` CLI command.
  - New optional dependency group `screensight[audio]` (`soundcard`, `numpy`).
  - Opt-in and off by default: requires both the master switch on **and**
    `SCREENSIGHT_ENABLE_AUDIO=1`. Duration is capped at 30s.
  - `audio.wav` is cleaned up on `screensight off`, alongside `frame.jpg`.
  - Loopback via `soundcard`: Windows (WASAPI) and Linux (PulseAudio monitor) work out of
    the box; macOS/WSL need a virtual output device (BlackHole/SoundFlower).
  - Optional PocketStation capture for one application or the default microphone on macOS,
    Windows, and Linux, without changing the existing screenshot or loopback recorders.

## [0.1.0] - 2026-08-11

Initial release. ScreenSight generalizes agent screen-awareness beyond a single
agent, shipping as an MCP server, a plain CLI, and a standalone watch daemon.

### Added

- **`core.capture_once()`** — the single capture choke point that composes every
  safety property (switch check → backend → blocklist → downscale/redact → hash).
- **CLI** (`screensight`) with `on`, `off`, `status`, `capture`, `watch`,
  `watch-stop`, `watch-status`, and `displays` verbs (stdlib `argparse`, no extra deps).
- **MCP server** (`screensight-mcp`) exposing 8 FastMCP tools: `screen_enable`,
  `screen_disable`, `screen_status`, `screen_capture`, `screen_watch_start`,
  `screen_watch_stop`, `screen_watch_latest`, `screen_list_displays`.
- **Watch daemon** (`watch.py`) — a detached background process that captures on an
  interval, skips unchanged frames, auto-stops after `MAX_FRAMES_PER_WATCH`, and
  turns the master switch off on exit.
- **Cross-platform capture backends** — Windows (PowerShell + System.Drawing, incl.
  a WSL subclass), macOS (`screencapture` + `osascript`), and Linux
  (`grim` / `gnome-screenshot` / `import`, `xdotool` for window titles).
- **Privacy layer** — master switch (off by default), sensitive-app blocklist,
  user-defined redaction zones, one-frame hygiene with cleanup on `off`, and
  1568px long-edge downscaling.
- **Installers** — `install.sh` and `install.ps1`, which print per-agent MCP config
  snippets and can install the legacy Claude Code skill adapter.
- **Legacy Claude Code skill adapter** (`skills/claude-code/SKILL.md`).
- **Ready-made MCP config examples** for Claude Code, Cursor, Windsurf, Cline,
  Codex, Continue, JetBrains, Zed, opencode, Roo Code, and mason.nvim (`examples/`).
- **Documentation** — `README.md`, `GUIDE.md`, `PROJECT.md`, `ARCHITECTURE.md`,
  `AGENTS.md`.
- **Test suite** — state on/off round-trip, blocklist matching, redact-zone scaling,
  diff hashing, and `capture_once()` with a mocked backend (no real screenshots).

### Platform status

- Windows — ✅ tested
- macOS, Linux, WSL — ⚠️ implemented but untested

[Unreleased]: https://github.com/himanshu231204/ScreenSight/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/himanshu231204/ScreenSight/releases/tag/v0.1.0
