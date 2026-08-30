# Troubleshooting

## "Capture failed: off"

The master switch is off. That's the default state.

```bash
screensight on
screensight capture
```

## "blocked: active window '…' matches the sensitive-app blocklist"

The current window title contains a blocklist term. Either:

1. Switch to a different window and capture again, or
2. Remove the term from `blocklist` in `~/.screensight/redact_zones.json`

Removing default terms widens what can be captured — see
[Configuration](../reference/configuration.md).

## "PowerShell capture failed" (Windows)

Confirm PowerShell is available and allowed to read the screen:

```bash
powershell.exe -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SystemInformation]::VirtualScreen"
```

## "Daemon already running"

A watch daemon is already active:

```bash
screensight watch-status
screensight watch-stop
```

If `watch-stop` can't find the process, the PID file may be stale — remove
`~/.screensight/daemon.pid` and try again.

## Frame file doesn't exist after capture

The capture may have failed silently. Check the switch, then run the capture with stderr
visible:

```bash
screensight status
screensight capture 2>&1
```

Also check `~/.screensight/screensight.log`.

## MCP server not starting

Verify the binary is on your PATH — the agent spawns it by name:

```bash
which screensight-mcp    # Linux / macOS
where screensight-mcp    # Windows
```

If it isn't found, reinstall:

```bash
pip install -e .
```

If it's installed in a virtualenv the agent doesn't share, put the absolute path in the
`command` field of your MCP config instead:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "/home/you/.venvs/screensight/bin/screensight-mcp"
    }
  }
}
```

## The agent doesn't see the tools at all

- Restart the agent after editing its MCP config — most read it only at startup.
- Check the config file location for your agent in
  [Agent setup](../get-started/agent-setup.md).
- Confirm the JSON parses (a trailing comma is the usual culprit).

## Linux: capture works but the window title is always null

The title lookup needs `xdotool` on X11. On Wayland the title may be unavailable
entirely — in which case the blocklist can't protect you, and captures should be treated
as unverified. Install `xdotool`, or capture only from windows you've checked yourself.

## Getting help

- `screensight --help` for CLI options
- `screensight status` for the current state
- `~/.screensight/screensight.log` for errors
- [Open an issue on GitHub](https://github.com/harshitboots/ScreenSight/issues)
