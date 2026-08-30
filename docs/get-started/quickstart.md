# Quickstart

Two minutes from a fresh clone to an agent that can see your screen.

## 1. Install

```bash
git clone https://github.com/harshitboots/ScreenSight screensight
cd screensight
pip install .
```

See [Installation](installation.md) for pipx and installer-script options.

## 2. Enable capture

The master switch is **off by default**. Nothing can capture until you turn it on.

```bash
screensight on
```

## 3. Take a screenshot

```bash
screensight capture
```

```json
{
  "path": "C:\\Users\\you\\.screensight\\frame.jpg",
  "sha256": "3d950ca5b88301d1f259bab41a35d6f0ffedd0694ead17c50e28aa4660d6dcf1",
  "active_window_title": "main.py - myproject - Visual Studio Code"
}
```

## 4. Check status

```bash
screensight status
```

## 5. Turn it off when you're done

```bash
screensight off
```

`off` flips the switch **and** deletes `~/.screensight/frame.jpg`.

---

## Point your agent at it

=== "MCP agent"

    Add this to your agent's MCP config, then restart the agent:

    ```json
    {
      "mcpServers": {
        "screensight": {
          "command": "screensight-mcp"
        }
      }
    }
    ```

    Ask it *"what's on my screen?"* — it will call `screen_capture` and describe the frame.
    Config file locations for each agent are listed in [Agent setup](agent-setup.md).

=== "No MCP (Aider, shell agents)"

    Add this to your agent instructions:

    ```text
    When I ask you to look at my screen, run:
      screensight capture

    The output will contain a "path" field with the screenshot location.
    Read that file to see what's on my screen.
    ```

---

## Watch a change over time

```bash
screensight watch --interval 3 --max-frames 15
screensight watch-status
screensight watch-stop
```

The daemon skips unchanged frames, stops itself after the frame budget, and turns the
master switch off on exit. See [Watch mode](../reference/watch-mode.md).

!!! tip "If a capture is refused"
    `Capture failed: off` means the master switch is off — run `screensight on`.
    A `blocked:` message means your active window title matched the sensitive-app
    blocklist; switch windows or edit the blocklist in
    [Configuration](../reference/configuration.md).
