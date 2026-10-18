# Configuration

Everything ScreenSight stores lives under `~/.screensight/`. There is no global config
file elsewhere and no remote state. Audio has a separate opt-in switch described below.

```text
~/.screensight/
  state.json          # Master on/off switch
  frame.jpg           # Latest captured frame
  audio.wav           # Latest captured system audio (if audio is used)
  daemon.json         # Watch daemon status
  daemon.pid          # Watch daemon process ID
  redact_zones.json   # Blocklist + redaction zones
  screensight.log     # Log file (if enabled)
```

| File | Written by | Read by | Purpose |
|---|---|---|---|
| `state.json` | `state.py` | `core.py` | Master on/off switch |
| `frame.jpg` | `core.py` via `privacy.process_frame` | CLI, MCP tools | The one current screenshot, overwritten each capture |
| `audio.wav` | `core.py` via `capture.audio` | CLI, MCP tools | The one current audio recording, overwritten each capture |
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

## Audio capture

Audio capture is **opt-in and off by default**. Two independent switches must both permit a
recording:

1. The master switch is on (`screensight on`).
2. The `SCREENSIGHT_ENABLE_AUDIO` environment variable is set to `1` (or `true`/`yes`).

```bash
pip install 'screensight[audio]'   # soundcard + numpy
export SCREENSIGHT_ENABLE_AUDIO=1
screensight capture-audio --duration 5

pip install 'screensight[pocketstation]'
screensight capture-audio --source application --application Zoom
screensight capture-audio --source microphone
```

| Setting | Default | Meaning |
|---|---|---|
| `SCREENSIGHT_ENABLE_AUDIO` | unset (off) | Must be `1`/`true`/`yes` to allow audio capture |
| duration | `5` | Seconds per capture, clamped to `1`–`30` |
| source | `system` | System output, one application, or the default microphone |
| sample rate | recorder-defined | `44100` Hz for system; `48000` Hz for PocketStation |

The optional extras map directly to the selected source: install `screensight[audio]` for
`system`, and install `screensight[pocketstation]` for `application` or `microphone`.

The recording is written to `~/.screensight/audio.wav` (a single reused file, like
`frame.jpg`) and deleted on `screensight off`.

**Loopback device support** — capture records what's playing through the default speaker:

| Platform | Status |
|---|---|
| Windows | ✅ WASAPI loopback, works out of the box |
| Linux | ✅ PulseAudio/PipeWire monitor source, works out of the box |
| macOS / WSL | ⚠️ requires a virtual output device (BlackHole or SoundFlower) set as the default output |

For one application, use PocketStation instead of changing the computer's default output:

```bash
screensight capture-audio --source application --application Zoom
screensight capture-audio --source application --application bundle:us.zoom.xos
screensight capture-audio --source application --application pid:1234
```

Display names must match one running application. Use a bundle ID when the display name is
not unique, or a process ID for one exact running instance. Microphone capture uses the
current default input device. Application selectors are required for `application` and are
rejected for `system` and `microphone`.

## Resetting

```bash
screensight off
rm -rf ~/.screensight
```

The directory is recreated with defaults on the next run.
