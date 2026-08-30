# CLI reference

The `screensight` command is the human- and shell-facing surface. It calls the same
`core.capture_once()` pipeline the MCP server uses, so every safety property applies
identically.

## Command summary

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

## Switch commands

| Command | What it does |
|---------|--------------|
| `screensight on` | Enable screen capture |
| `screensight off` | Disable capture **and** delete `frame.jpg` |
| `screensight status` | Print whether capture is enabled |

## `screensight capture`

Captures one frame and prints a JSON object.

```bash
screensight capture              # primary display
screensight capture --display 1  # a specific display index
```

```json
{
  "path": "C:\\Users\\you\\.screensight\\frame.jpg",
  "sha256": "3d950ca5b883...",
  "active_window_title": "main.py - VS Code"
}
```

| Field | Meaning |
|---|---|
| `path` | Absolute path to the written frame |
| `sha256` | Hash of the processed frame, used for change detection |
| `active_window_title` | Best-effort window title; `null` when the platform can't determine it |

!!! warning "A null title is not a safe title"
    When `active_window_title` is `null`, the backend could not determine the foreground
    window. Callers must treat that as *not verified safe*, never as *safe*.

## `screensight displays`

```bash
screensight displays
```

```text
Available displays:
  Display 0: primary (1920x1080)
  Display 1: secondary (2560x1440)
```

Pass an index from this list to `capture --display`.

## Watch commands

```bash
screensight watch                                  # every 5s, max 10 frames
screensight watch --interval 3 --max-frames 20     # custom
screensight watch-status                           # daemon progress
screensight watch-stop                             # stop early
```

| Flag | Default | Meaning |
|---|---|---|
| `--interval` | `5` | Seconds between captures |
| `--max-frames` | `10` | Changed frames before the daemon auto-stops |

`watch-status` prints the daemon's live state:

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

Full behaviour is documented in [Watch mode](watch-mode.md).

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `3` | Master switch is off, or capture failed |

Exit code `3` is the one to branch on in scripts — it covers both "you never turned it on"
and "the capture was refused or failed".

```bash
if screensight capture > frame.json; then
  echo "captured: $(jq -r .path frame.json)"
else
  echo "no frame (switch off or capture refused)" >&2
fi
```
