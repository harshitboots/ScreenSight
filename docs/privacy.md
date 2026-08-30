# Privacy & security

Privacy is the design constraint ScreenSight is built around, not a feature bolted on
afterwards. Six properties hold, and they hold for every surface — CLI, MCP server and
watch daemon alike — because all three go through the same `core.capture_once()` pipeline.

## 1. Off by default

The master switch lives at `~/.screensight/state.json` and gates every capture.

```bash
screensight status   # is it on?
screensight on       # enable capture
screensight off      # disable capture + delete the frame
```

The check happens **inside** `core.capture_once()` — not in a prompt, not in a tool
description. No instruction, injected or otherwise, can talk the tool into capturing while
the switch is off.

## 2. Sensitive-app blocklist

Before a frame is written, the active window title is checked against a blocklist. On a
match the capture aborts: nothing is saved, nothing is sent.

Default blocklist:

- 1Password, Bitwarden, KeePass, LastPass
- Keychain Access
- Private browsing / Incognito windows
- Any window with "password" in the title

Extend it in `~/.screensight/redact_zones.json`:

```json
{
  "blocklist": ["1password", "bitwarden", "my-bank-app"],
  "zones": []
}
```

!!! warning "Unknown titles are not trusted"
    When a platform backend can't determine the foreground window it returns `None`.
    Every caller treats that as *not verified safe* — never as *safe*.

## 3. Zone redaction

Define fixed screen rectangles that are always blacked out before the frame is saved —
useful for a permanent on-screen element like a clock widget, a notes app, or a banking
tool parked in one corner.

```json
{
  "zones": [
    {"x": 0, "y": 0, "w": 200, "h": 100, "label": "top-left corner"},
    {"x": 1700, "y": 0, "w": 220, "h": 40, "label": "system tray"}
  ]
}
```

## 4. Frame hygiene

- One file: `~/.screensight/frame.jpg`
- Overwritten on every capture — it never accumulates a folder of screenshots
- Deleted when you run `screensight off`

There is no history, no database, and no upload. Only the daemon's status
(`daemon.json`) and PID (`daemon.pid`) sit alongside it.

## 5. Watch mode self-limits

- Default budget: 10 changed frames per watch session
- Auto-stops once `--max-frames` is reached
- Turns the master switch **off** when it exits

An idle daemon can't quietly keep running and burning tokens.

## 6. Downscale to 1568px

Every image is resized to a 1568px long edge before it leaves disk — the point past which
more pixels don't help a vision model. It bounds token cost for every consumer, and it
means less detail leaves your machine than was on screen.

---

## What ScreenSight never does

- No API key, no account, no telemetry
- No network calls of its own — the frame goes to the agent that asked for it, nothing else
- No screenshot library and no background service; captures are native OS tool calls made
  on demand
- No frame retention beyond the single current `frame.jpg`

## Threat model, briefly

The property being defended is: *a capture happens only when the user has enabled it, and
never of a window the user marked sensitive.* The enforcement point is a single function
that every surface must call. If a second code path ever calls a `capture/*.py` backend
directly, the safety properties can silently diverge between surfaces — that is a bug, not
a style preference. See [Architecture](architecture.md).
