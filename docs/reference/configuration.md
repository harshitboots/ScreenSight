# Configuration

Everything ScreenSight stores lives under `~/.screensight/`. There is no global config
file elsewhere, no environment-variable layer, and no remote state.

```text
~/.screensight/
  state.json          # Master on/off switch
  frame.jpg           # Latest captured frame
  daemon.json         # Watch daemon status
  daemon.pid          # Watch daemon process ID
  redact_zones.json   # Blocklist + redaction zones
  screensight.log     # Log file (if enabled)
```

| File | Written by | Read by | Purpose |
|---|---|---|---|
| `state.json` | `state.py` | `core.py` | Master on/off switch |
| `frame.jpg` | `core.py` via `privacy.process_frame` | CLI, MCP tools | The one current screenshot, overwritten each capture |
| `redact_zones.json` | You (or your agent) | `privacy.py` | Blocklist terms + redaction rectangles |
| `daemon.json` | `watch.py` | CLI `watch-status`, MCP `screen_watch_latest` | Running state, frame count, last change |
| `daemon.pid` | `watch.py` on start | `watch.py` on stop | Lets `watch-stop` find the process |

## redact_zones.json

The only file you'll normally hand-edit. It holds two independent lists.

```json
{
  "blocklist": [
    "1password",
    "bitwarden",
    "keychain access",
    "keepass",
    "lastpass",
    "password",
    "private browsing",
    "incognito"
  ],
  "zones": [
    {"x": 0, "y": 0, "w": 200, "h": 100, "label": "optional label"}
  ]
}
```

### blocklist

Case-insensitive substrings matched against the **active window title** before a frame is
written. A match aborts the capture — nothing is saved, nothing is sent. Add your own
terms for anything else that should never be captured:

```json
{
  "blocklist": ["1password", "bitwarden", "my-banking-app"],
  "zones": []
}
```

Adding terms is always safe. Removing the defaults widens what can be captured — do it
deliberately.

### zones

Fixed rectangles blacked out on every frame before it's saved. Useful for permanent
on-screen elements: a notification corner, a system tray, a always-visible note widget.

```json
{
  "zones": [
    {"x": 0, "y": 0, "w": 200, "h": 100, "label": "notification area"},
    {"x": 1700, "y": 0, "w": 220, "h": 40, "label": "system tray"}
  ]
}
```

| Key | Meaning |
|---|---|
| `x`, `y` | Top-left corner, in screen pixels |
| `w`, `h` | Width and height, in screen pixels |
| `label` | Optional, for your own reference |

Zones are given in screen coordinates and scaled with the frame during downscaling, so you
don't need to account for the 1568px resize yourself.

## state.json

Managed by `screensight on` / `off`. It's the master switch, and `core.capture_once()`
re-reads it on every single capture — including each tick of the watch daemon.

```bash
screensight status   # read
screensight on       # enable
screensight off      # disable + delete frame.jpg
```

## Resetting

```bash
screensight off
rm -rf ~/.screensight
```

The directory is recreated with defaults on the next run.
