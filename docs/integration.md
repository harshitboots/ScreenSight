# Integration Guide

Complete, practical guide for connecting the ScreenSight MCP server to **OpenCode** and **Claude** products.

---

## Table of contents

1. [OpenCode integration](#opencode-integration)
2. [Claude integration](#claude-integration)
3. [Recommended Windows setup](#recommended-windows-setup)
4. [Troubleshooting](#troubleshooting)
5. [Common errors reference table](#common-errors-reference-table)

---

## OpenCode integration

OpenCode uses its own MCP configuration schema — **not** the `mcpServers` format used by Claude, Cursor, or Windsurf. The project ships two configuration examples:

| Source | Format |
|--------|--------|
| `examples/mcp_config_opencode.json` | Legacy `mcpServers` format (for older OpenCode versions) |
| `opencode.json` (repo root) | Current `mcp` format with `type: "local"` (for current OpenCode versions) |

### Where to place the config file

Place `opencode.json` in your **project root** (the directory where you run `opencode`).

OpenCode reads `opencode.json` from the current working directory. If you are working in a different folder (e.g. `C:\Users\you\your project`), place the file there — not in the ScreenSight repo.

### Option A: PATH-based command

If `screensight-mcp` is globally available (installed via `pip install -e .` or `pipx install screensight` from the ScreenSight repo):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "screensight": {
      "type": "local",
      "command": [
        "screensight-mcp"
      ],
      "enabled": true
    }
  }
}
```

### Option B: Windows absolute path (virtual environment)

If ScreenSight is installed inside a `.venv` — which is the case for a source checkout — use the full path to the executable inside that venv:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "screensight": {
      "type": "local",
      "command": [
        "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
      ],
      "enabled": true
    }
  }
}
```

Replace `<USERNAME>` with your actual Windows username. For example, if your user folder is `C:\Users\<USERNAME>`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "screensight": {
      "type": "local",
      "command": [
        "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
      ],
      "enabled": true
    }
  }
}
```

> **Important:** The `command` field is an **array**, not a string. Each element is one argument. The executable path goes in the first (and usually only) element.

### Verify the connection

After saving `opencode.json`, restart OpenCode completely, then run:

```powershell
opencode mcp list
```

**Successful output** looks like this — you should see `screensight` listed with its tools:

```
MCP Servers:
  screensight (local)
    Tools:
      - screen_enable
      - screen_disable
      - screen_status
      - screen_capture
      - screen_watch_start
      - screen_watch_stop
      - screen_watch_latest
      - screen_list_displays
```

If `screensight` does not appear, see [Troubleshooting: MCP server not shown in opencode mcp list](#a-mcp-server-not-shown-in-opencode-mcp-list).

---

## Claude integration

Claude has two products that support MCP: **Claude Code** (the CLI/terminal agent) and **Claude Desktop** (the GUI app). They use different configuration formats and file locations.

### Claude Code

Claude Code uses the standard `mcpServers` JSON format.

#### Project-level configuration (recommended)

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

#### Global configuration

Add the same block to `~/.claude.json` (your home directory):

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

#### Windows absolute path (virtual environment)

If `screensight-mcp` is not on your PATH, use the full path:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
    }
  }
}
```

#### Verify

After restarting Claude Code:

```bash
claude mcp list
```

You should see `screensight` listed.

### Claude Desktop

Claude Desktop uses the same `mcpServers` format as Claude Code, but the configuration file lives in a different location.

#### Configuration file location

| OS | Path |
|----|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

#### Configuration (PATH-based)

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

#### Configuration (Windows absolute path)

```json
{
  "mcpServers": {
    "screensight": {
      "command": "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
    }
  }
}
```

#### Verify

After restarting Claude Desktop, open the MCP settings panel (click the hammer icon in the chat input area). You should see `screensight` listed with its 8 tools.

### Legacy skill adapter (Claude Code only)

If you previously used the `/claude-screen` slash-command approach, you can install the legacy skill adapter:

```bash
bash install.sh --with-claude-skill
```

This copies a `SKILL.md` file to `~/.claude/skills/`. The MCP server is the supported path going forward — the skill adapter is kept for backward compatibility only.

---

## Recommended Windows setup

Step-by-step workflow for a fresh Windows installation.

### 1. Clone and install

```powershell
git clone https://github.com/harshitboots/ScreenSight.git
cd ScreenSight
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Verify CLI tools work

```powershell
screensight --help
screensight-mcp --help
```

Both commands should print help text without errors.

### 3. Find the MCP executable path

```powershell
(Get-Command screensight-mcp).Source
```

Example output:

```
C:\Users\<USERNAME>\ScreenSight\.venv\Scripts\screensight-mcp.exe
```

Copy this path — you will need it for the MCP configuration.

### 4. Add MCP configuration

**For OpenCode:** Create `opencode.json` in your working directory (e.g. `C:\Users\<USERNAME>\TripG\opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "screensight": {
      "type": "local",
      "command": [
        "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
      ],
      "enabled": true
    }
  }
}
```

**For Claude Code:** Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
    }
  }
}
```

**For Claude Desktop:** Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
    }
  }
}
```

### 5. Restart the MCP client

Close and reopen your MCP client (OpenCode, Claude Code, or Claude Desktop). MCP configurations are read at startup — changes require a restart.

### 6. Verify the MCP connection

**OpenCode:**

```powershell
opencode mcp list
```

**Claude Code:**

```bash
claude mcp list
```

You should see `screensight` listed with its tools.

### 7. Turn ScreenSight on

```powershell
screensight on
```

MCP being connected does **not** automatically mean screen capture is enabled. The master switch must be ON before any capture can work.

### 8. Test a real capture

Ask your agent:

> "Use ScreenSight MCP to capture and analyze my current screen. Do not guess."

If the agent calls `screen_capture` and returns a description of your screen, the integration is working.

---

## Troubleshooting

### A. MCP server not shown in `opencode mcp list`

**Symptoms:** `opencode mcp list` does not show `screensight`, or shows it with an error status.

**Possible causes:**

1. Wrong config file location — OpenCode reads `opencode.json` from the **current working directory**, not from the ScreenSight repo.
2. Incorrect OpenCode MCP JSON schema — OpenCode uses `mcp` with `type: "local"`, not `mcpServers`.
3. Using an old/new OpenCode config syntax that doesn't match your installed version.
4. The `screensight-mcp` command is not on your PATH.

**Diagnostic steps:**

```powershell
# Check if screensight-mcp is on PATH
Get-Command screensight-mcp

# Find the exact path
(Get-Command screensight-mcp).Source

# Test that the command runs
screensight-mcp --help

# Check if it's on the system PATH
where.exe screensight-mcp
```

**Solutions:**

- If `Get-Command` fails, the executable is not on PATH. Use the absolute path in your config instead.
- If `Get-Command` succeeds but the tool still doesn't appear, verify your config file location and JSON syntax.
- Check that you are using the correct schema for your OpenCode version (see below).

### B. "Configuration is invalid" or "Expected { readonly 'type': 'local', ... }"

**Error message:**

```
Configuration is invalid
Expected { readonly "type": "local", ... } | { readonly "type": "remote", ... }
```

and/or:

```
Missing key mcp.servers.enabled
```

**Cause:** OpenCode version/schema mismatch. Different versions of OpenCode expect different config schemas. The `mcpServers` format from older documentation or from other agents (Claude, Cursor) does **not** work with current OpenCode versions.

**Solution:** Use the schema that matches your installed OpenCode version. The configuration pattern that the current version accepts:

```json
{
  "mcp": {
    "screensight": {
      "type": "local",
      "command": [
        "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
      ],
      "enabled": true
    }
  }
}
```

> **Version-dependent:** This schema includes `type`, `command` (as an array), and `enabled`. If your OpenCode version expects a different structure, check the OpenCode documentation or run `opencode --help` for configuration guidance. Do not blindly copy a configuration from documentation for a different version.

### C. "MCP error -32000: Connection closed"

**Error message:**

```
MCP error -32000: Connection closed
```

**Possible causes:**

1. The MCP process starts but immediately exits.
2. Wrong executable path — the file doesn't exist or isn't a valid Python entry point.
3. Wrong Python virtual environment — the command exists but its dependencies aren't installed.
4. Dependencies are installed only inside the ScreenSight `.venv`, not in the global Python.
5. The command works inside the ScreenSight folder but not from your working directory (because the venv isn't activated there).

**Diagnostic steps:**

```powershell
# Verify the command exists
Get-Command screensight-mcp

# Get the exact path
(Get-Command screensight-mcp).Source

# Test it directly
screensight-mcp --help

# Check where the system finds it
where.exe screensight-mcp

# If using an absolute path, verify the file exists
Test-Path "C:\Users\<USERNAME>\ScreenSight\.venv\Scripts\screensight-mcp.exe"
```

**Solution:** Use the absolute path to the `.venv` executable in your MCP config:

```json
{
  "mcp": {
    "screensight": {
      "type": "local",
      "command": [
        "C:\\Users\\<USERNAME>\\ScreenSight\\.venv\\Scripts\\screensight-mcp.exe"
      ],
      "enabled": true
    }
  }
}
```

This ensures the MCP server runs in the correct Python environment with all dependencies available, regardless of where your MCP client is running from.

### D. ScreenSight master switch

MCP being connected does **not** mean screen capture is enabled. The master switch is off by default.

```powershell
# Turn it on
screensight on

# Check status
screensight status

# Turn it off when done
screensight off
```

Or let the agent enable it by calling the `screen_enable` tool.

### E. How to verify that OpenCode is actually using ScreenSight

There is a difference between:

- **"MCP connected"** — the server started and listed its tools.
- **"MCP tool actually called"** — the agent decided to use a ScreenSight tool.

To confirm the agent is actually calling ScreenSight tools, look for tool activity such as:

- `screensight_screen_capture`
- `screensight_screen_list_displays`
- `screensight_screen_watch_start`

**Direct test prompt:**

> "Use ScreenSight MCP to capture and analyze my current screen. Do not guess."

Seeing an actual ScreenSight tool call in the agent's output confirms that OpenCode is attempting to use the MCP. If the agent replies without calling any tool, it may not recognize the tool names or may be choosing not to use them.

### F. Capture / output validation error

**Error message:**

```
outputSchema defined but no structured output returned
```

**Symptoms:**

- `screen_status` works.
- `screen_list_displays` works.
- ScreenSight is enabled (`screensight on`).
- `screen_capture` consistently fails with the above error.

**Cause:** This is an MCP server image/structured output serialization issue, not a Windows permissions issue or a master switch issue. FastMCP auto-generates an `outputSchema` from the function's return type annotation. The `screen_capture` function returns `[Image(...), "text string"]`, but the `Image` object (a plain Python class, not a Pydantic model) doesn't serialize cleanly through Pydantic's JSON serializer. The MCP client receives the declared `outputSchema`, tries to validate `structured_content` against it, and rejects the malformed result.

**Diagnostic steps:**

```powershell
# Check FastMCP version
pip show fastmcp

# Check which repo you are using
git remote -v

# Check the latest commit
git log -1 --oneline
```

**Solution:** This repository includes a fix for this issue. The `screen_capture` tool decorator uses `output_schema=None` to prevent FastMCP from auto-generating a schema that would fail validation. If you are using the current `main` branch or the `fix/screen-capture-output-schema` branch, this fix is already applied.

To verify you have the fix:

```powershell
# Check that output_schema=None is set
Select-String -Path "src\screensight\mcp_server.py" -Pattern "output_schema=None"
```

If this returns a match, the fix is present. If not, update your branch:

```powershell
git pull origin main
pip install -e .
```

> **Note:** Reinstalling alone will not fix this if the source code doesn't contain the fix. The issue is in the MCP server code, not in the installation method.

---

## Common errors reference table

| Error | Likely cause | Solution |
|-------|-------------|----------|
| "Capture failed: off" | Master switch is off | Run `screensight on` or have the agent call `screen_enable` |
| "blocked: active window '...' matches the sensitive-app blocklist" | Current window title contains a blocklist term | Switch to a different window, or edit `~/.screensight/redact_zones.json` |
| "Daemon already running" | A watch daemon is already active | Run `screensight watch-stop`, then retry |
| "MCP server not shown in opencode mcp list" | Wrong config location or wrong schema | Place `opencode.json` in your working directory; use `mcp` schema with `type: "local"` |
| "Configuration is invalid" / "Expected { readonly 'type': 'local', ... }" | OpenCode version/schema mismatch | Use the `mcp` schema matching your OpenCode version, not `mcpServers` |
| "MCP error -32000: Connection closed" | MCP process exits immediately; wrong path or missing deps | Use absolute path to `.venv\Scripts\screensight-mcp.exe`; ensure deps are installed |
| "outputSchema defined but no structured output returned" | FastMCP schema serialization issue with Image object | Update to latest `main` branch which includes the `output_schema=None` fix |
| Agent doesn't see tools at all | Config not loaded; JSON syntax error | Restart agent after editing config; check for trailing commas in JSON |
| Window title always null (Linux) | Missing `xdotool` on X11, or running on Wayland | Install `xdotool`; on Wayland, titles may be unavailable |
| Frame file doesn't exist after capture | Capture failed silently | Run `screensight status` and `screensight capture 2>&1`; check `~/.screensight/screensight.log` |

---

## Getting help

- `screensight --help` for CLI options
- `screensight status` for the current state
- `~/.screensight/screensight.log` for error logs
- [GitHub Issues](https://github.com/harshitboots/ScreenSight/issues) for bugs and feature requests
