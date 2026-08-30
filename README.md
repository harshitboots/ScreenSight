# ScreenSight

**Let *any* coding agent see your screen — not just Claude Code.**

MCP server + CLI fallback + a standalone watch daemon. No API key required; runs on whatever subscription/session the agent already has.

ScreenSight generalizes screen-awareness beyond a single agent. It ships as:

- **MCP server** — works in Cursor, Windsurf, Cline, Claude Code, Codex CLI, and any MCP-capable agent
- **CLI** — works for Aider, raw shell agents, or any environment that can run a command
- **Watch daemon** — a long-lived background process for interval capture with automatic stop

Inspired by [ScreenPipe](https://github.com/mediar-ai/screenpipe) — this is the agent-agnostic version.

## Install

### From source (recommended)

```bash
git clone <repo-url> screensight
cd screensight

# Linux / macOS
bash install.sh

# Windows
.\install.ps1
```

### With pip directly

```bash
pip install .
```

### With pipx

```bash
pipx install .
```

Requires **Python 3.10+**.

## MCP Configuration

Add this block to your agent's config file:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

| Agent | Config file location |
|-------|---------------------|
| Claude Code | `~/.claude.json` or project `.mcp.json` |
| Cursor | `~/.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Cline | VS Code settings under `cline.mcpServers` |
| Codex CLI | `~/.codex/config.json` |
| Aider / no MCP | No config needed — use the CLI directly |

### MCP Tools (8 total)

| Tool | Description |
|------|-------------|
| `screen_enable` | Turn ON the master switch |
| `screen_disable` | Turn OFF the master switch |
| `screen_status` | Check whether capture is enabled |
| `screen_capture` | Capture screen, returns image + window title |
| `screen_watch_start` | Start bounded watch daemon |
| `screen_watch_stop` | Stop watch daemon |
| `screen_watch_latest` | Get daemon status and frame count |
| `screen_list_displays` | List available monitors |

## CLI Usage

```bash
screensight on                          # Enable capture
screensight off                         # Disable capture (deletes frame)
screensight status                      # Check switch state
screensight capture                     # Capture primary display
screensight capture --display 1         # Capture specific display
screensight watch --interval 5          # Watch every 5s (default)
screensight watch --interval 3 --max-frames 20
screensight watch-stop                  # Stop watch daemon
screensight watch-status                # Check daemon status
screensight displays                    # List monitors
```

### Example output

```json
// screensight capture
{
  "path": "C:\\Users\\you\\.screensight\\frame.jpg",
  "sha256": "3d950ca5b88301d1f259bab41a35d6f0ffedd0694ead17c50e28aa4660d6dcf1",
  "active_window_title": "main.py - myproject - Visual Studio Code"
}
```

```json
// screensight watch-status
{
  "frames_analyzed": 3,
  "last_hash": "15dc34902d50de22a1146a9d8b9dd732f9e5c60d9dfbb41bc5b7f5a72e5bbb8b",
  "interval": 5,
  "max_frames": 10,
  "status": "running",
  "running": true
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `3` | Master switch is off, or capture failed |

## Privacy

ScreenSight is designed with privacy as a first-class concern. Nothing is captured unless you explicitly enable it.

### 1. Off by default

The master switch (`~/.screensight/state.json`) gates every capture. The check happens inside `core.capture_once()` — not in a prompt or tool description — so no instruction injection can bypass it.

```bash
screensight status   # Check if it's on
screensight on       # Enable capture
screensight off      # Disable capture + delete frame
```

### 2. Sensitive-app blocklist

Before a frame is saved, the active window title is checked against a blocklist. Matches abort the capture — nothing is saved, nothing is sent.

**Default blocklist:**
- 1Password, Bitwarden, KeePass, LastPass
- Keychain Access
- Private browsing / Incognito windows
- Any window with "password" in the title

**Customize:** Edit `~/.screensight/redact_zones.json`:

```json
{
  "blocklist": ["1password", "bitwarden", "my-bank-app"],
  "zones": []
}
```

### 3. Zone redaction

Define fixed screen rectangles that always get blacked out before the frame is saved. Useful for permanent on-screen elements like clock widgets, note apps, or banking tools.

```json
{
  "zones": [
    {"x": 0, "y": 0, "w": 200, "h": 100, "label": "top-left corner"}
  ]
}
```

### 4. Frame hygiene

- One frame file: `~/.screensight/frame.jpg`
- Overwritten on every capture — never accumulates
- Deleted on `screensight off`
- Daemon status: `~/.screensight/daemon.json`
- Daemon PID: `~/.screensight/daemon.pid`

### 5. Watch mode self-limits

- Default max: 10 changed frames per watch session
- Auto-stops after `--max-frames` reached
- Turns off the master switch when it exits
- Prevents idle daemons from quietly burning tokens

### 6. Downscale to 1568px

Images are downscaled to 1568px long edge before leaving disk — the point past which more pixels don't help a vision model. Keeps token cost low for all consumers.

## Project structure

```
src/screensight/
  __init__.py          # Package init
  __main__.py          # CLI entry point (argparse)
  config.py            # Paths, constants, blocklist defaults
  state.py             # Master on/off switch
  core.py              # capture_once() — single entrypoint
  privacy.py           # Blocklist check, downscale + zone redaction
  diff.py              # SHA-256 hashing, change detection
  watch.py             # Daemon (start/stop/status + loop)
  mcp_server.py        # FastMCP server (8 tools)
  capture/
    base.py            # CaptureBackend ABC
    macos.py           # macOS (screencapture + osascript)
    linux.py           # Linux (grim / gnome-screenshot / import)
    windows.py         # Windows + WSL (PowerShell + System.Drawing)

tests/
  test_state.py        # On/off round trip
  test_privacy.py      # Blocklist matching, zone scaling
  test_diff.py         # Hash stability, change detection
  test_core.py         # capture_once() with mocked backend
  test_wsl.py          # WSL capture backend tests
```

## Comparison

| Feature | ScreenSight | ScreenPipe | Agent-specific tools |
|---------|:-----------:|:----------:|:--------------------:|
| Works with any MCP agent | ✅ | ❌ | ❌ |
| CLI fallback (no MCP needed) | ✅ | ❌ | Varies |
| Watch daemon with auto-stop | ✅ | ✅ | ❌ |
| Master switch (off by default) | ✅ | ❌ | Varies |
| Blocklist + zone redaction | ✅ | ❌ | ❌ |
| No API key required | ✅ | ✅ | Varies |
| Cross-platform | ✅ | ✅ | Varies |
| 1568px downscale for tokens | ✅ | ❌ | ❌ |
| Frame cleanup on off | ✅ | ❌ | ❌ |
| Open source | ✅ | ✅ | Varies |

## Development

```bash
# Create venv and install in editable mode
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.\.venv\Scripts\Activate.ps1     # Windows

pip install -e .
pip install pytest               # For running tests

# Run tests
pytest tests/ -v

# Run the MCP server for testing
screensight-mcp                  # Starts on stdio
fastmcp dev screensight.mcp_server:mcp   # Or via fastmcp dev
```

## Platform support

| Platform | Status | Backend |
|----------|--------|---------|
| Windows | ✅ Tested | PowerShell + System.Drawing |
| macOS | ⚠️ Untested | screencapture + osascript |
| Linux | ⚠️ Untested | grim / gnome-screenshot / import + xdotool |
| WSL2 | ✅ Tested | PowerShell (captures Windows host desktop) |

### WSL2 Support

ScreenSight supports capturing the Windows host screen from inside WSL2. This requires:

**Prerequisites:**
- WSL2 (not WSL1) with a recent Ubuntu/Debian distribution
- `powershell.exe` accessible from WSL PATH (usually automatic)
- `wslpath` utility (included in most WSL2 distributions)

**How it works:**
1. Detects WSL environment via `platform.uname().release` containing "microsoft"
2. Invokes `powershell.exe` to capture the Windows desktop using System.Drawing
3. Converts the Windows temp path to WSL path via `wslpath`
4. Copies the frame bytes across the filesystem boundary
5. Cleans up the Windows temp file

**Known limitations:**
- WSL1 is not supported (different path translation mechanism)
- Some display configurations may not list correctly
- PowerShell execution policy may block scripts (use `-ExecutionPolicy Bypass` if needed)

**Troubleshooting:**
```bash
# Verify WSL2 is running
wsl.exe --list --verbose

# Test PowerShell access from WSL
powershell.exe -NoProfile -Command "echo hello"

# Test wslpath
wslpath -u "C:\\Users"
```

## License

MIT
