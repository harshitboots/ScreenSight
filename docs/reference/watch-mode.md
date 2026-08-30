# Watch mode

Watch mode is a detached background daemon that captures your screen at a fixed interval.
It's useful for:

- Monitoring changes over time
- Letting an agent observe a long-running process
- Debugging issues that only happen intermittently

## How it works

1. `screensight watch` spawns a detached background process.
2. The daemon calls `capture_once()` every *N* seconds.
3. Unchanged frames are skipped — SHA-256 of the processed frame is compared to the last one.
4. After `max_frames` **changed** frames, the daemon auto-stops.
5. The master switch is turned off when it exits.

The frame budget counts changed frames, not ticks. A screen that sits still costs nothing.

!!! note "Why a separate process"
    The MCP server's lifetime is tied to the agent session — often stdio, often
    per-request. That's the wrong lifetime for "check my screen every 5 seconds", so the
    loop lives in its own process that the CLI and MCP server start, poll and stop.

## Example workflow

```bash
# Start watching every 3 seconds, max 15 changed frames
screensight watch --interval 3 --max-frames 15

# ... do your work ...

# Check progress
screensight watch-status
# {"frames_analyzed": 5, "status": "running", ...}

# Stop early if needed
screensight watch-stop

# Or let it run — it stops itself after 15 changed frames
```

From an MCP agent the same three steps are `screen_watch_start`, `screen_watch_latest`
and `screen_watch_stop`.

## Status payload

```json
{
  "frames_analyzed": 3,
  "last_hash": "15dc34902d50de22a1146a9d8b9dd732f9e5c60d9dfbb41bc5b7f5a72e5bbb8b",
  "interval": 5,
  "max_frames": 10,
  "status": "running",
  "running": true
}
```

| Field | Meaning |
|---|---|
| `frames_analyzed` | Changed frames captured so far |
| `last_hash` | SHA-256 of the most recent frame |
| `interval` | Seconds between ticks |
| `max_frames` | Budget after which the daemon stops itself |
| `status` / `running` | Daemon lifecycle state |

## Files created

| File | Purpose |
|------|---------|
| `~/.screensight/frame.jpg` | Latest captured frame |
| `~/.screensight/daemon.json` | Daemon status and stats |
| `~/.screensight/daemon.pid` | Daemon process ID, so `watch-stop` can find it |

## Self-limits

- Default budget: **10** changed frames per session
- Auto-stops once `--max-frames` is reached
- Turns the master switch off on exit
- Prevents an idle daemon from quietly burning tokens in the background

If a start fails with *"daemon already running"*, one is already active — check it with
`screensight watch-status` or stop it with `screensight watch-stop`.
