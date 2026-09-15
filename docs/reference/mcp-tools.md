# MCP tools reference

The MCP server (`screensight-mcp`) exposes **nine tools** over stdio. Unlike the CLI, the
capture tools return MCP `Image`/`Audio` content blocks rather than file paths, so the
calling agent looks at the frame (or listens to the audio) in its own context instead of
reading a file off disk.

| Tool | Description |
|------|-------------|
| [`screen_enable`](#screen_enable) | Turn ON the master switch |
| [`screen_disable`](#screen_disable) | Turn OFF the master switch |
| [`screen_status`](#screen_status) | Check whether capture is enabled |
| [`screen_capture`](#screen_capture) | Capture screen, returns image + window title |
| [`screen_capture_audio`](#screen_capture_audio) | Record system, app, or mic audio |
| [`screen_watch_start`](#screen_watch_start) | Start the bounded watch daemon |
| [`screen_watch_stop`](#screen_watch_stop) | Stop the watch daemon |
| [`screen_watch_latest`](#screen_watch_latest) | Daemon status and frame count |
| [`screen_list_displays`](#screen_list_displays) | List available monitors |

---

## screen_enable

Turn on the master switch. Must be called before any capture succeeds.

```text
Input: none
Output: "ScreenSight enabled. State: {'enabled': True, ...}"
```

## screen_disable

Turn off the master switch. Stops any running watch daemon and deletes the frame.

```text
Input: none
Output: "ScreenSight disabled. State: {'enabled': False, ...}"
```

## screen_status

Check whether the master switch is on or off.

```text
Input: none
Output: "ScreenSight is ON. Details: {'enabled': True, ...}"
```

## screen_capture

Capture the screen and return the image to the agent.

```text
Input:
  - question (optional): text echoed back for context
  - display  (optional): display index; omit for primary
Output: Image content block + text with window title, path and hash
```

Ask your agent *"what's on my screen?"* and it will call this tool, receive the image, and
describe what it sees.

!!! info "The switch is enforced below this tool"
    `screen_capture` calls `core.capture_once()`, which re-reads the master switch and the
    blocklist itself. No tool description, prompt or injected instruction can talk the
    server into capturing while the switch is off.

## screen_capture_audio

Record system output, one desktop application, or the default microphone and return it to
the agent.

```text
Input:
  - duration (default 5):  seconds to record (clamped to 1–30)
  - source (default system): system, application, or microphone
  - application: exact name, bundle:<id>, or pid:<number>; set only for application
  - question (optional):   text echoed back for context
Output: Audio content block (WAV) + text with duration, sample rate and path
```

**Opt-in and off by default.** Beyond the master switch, audio requires the
`SCREENSIGHT_ENABLE_AUDIO=1` environment variable. Install `screensight[audio]` for system
output or `screensight[pocketstation]` for an application or microphone. If the selected
recorder is unavailable, the tool explains what to install and does not change ScreenSight's
existing system-audio behavior. `application` is required when `source=application` and is
rejected for `system` and `microphone` so a selector is never silently ignored.

PocketStation application capture does not require BlackHole, SoundFlower, Stereo Mix, or a
PulseAudio monitor. System capture remains available through the existing loopback recorder.
The `audio.wav` file is deleted on `screen_disable`.

!!! info "The switch is enforced below this tool"
    Like `screen_capture`, this tool calls into `core.capture_audio()`, which re-checks the
    master switch and the `SCREENSIGHT_ENABLE_AUDIO` gate itself — no prompt can talk the
    server into recording while either is off.

## screen_watch_start

Start a detached background daemon that captures on an interval.

```text
Input:
  - interval   (default 5):  seconds between captures
  - max_frames (default 10): changed frames before auto-stop
Output: "Watch daemon started: {'running': True, 'pid': 12345, ...}"
```

## screen_watch_stop

Stop the running daemon.

```text
Input: none
Output: "Watch daemon stopped: {'running': False, ...}"
```

## screen_watch_latest

Poll the daemon's progress.

```text
Input: none
Output:
  Daemon running: True
  Status: running
  Frames analyzed: 3
  Last hash: 15dc34902d50...
  Interval: 5s
  Max frames: 10
```

## screen_list_displays

List available monitors, so `screen_capture` can target one by index.

```text
Input: none
Output:
  Available displays:
    Display 0: primary (1920x1080)
    Display 1: secondary (2560x1440)
```

---

## Running the server directly

```bash
screensight-mcp                          # stdio server, for an agent to spawn
fastmcp dev screensight.mcp_server:mcp   # dev inspector
```

Configuration snippets for each agent are in [Agent setup](../get-started/agent-setup.md).
