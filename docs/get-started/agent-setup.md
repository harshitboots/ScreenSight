# Agent setup

Every MCP-capable agent takes the same server block. Only the file it goes in changes.

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

| Agent | Config file |
|-------|-------------|
| Claude Code | `~/.claude.json` or project `.mcp.json` |
| Cursor | `~/.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Cline | VS Code settings, under `cline.mcpServers` |
| Codex CLI | `~/.codex/config.json` |
| Aider / no MCP | No config — call the CLI directly |

Ready-made snippets for each agent also ship in the repo under [`examples/`](https://github.com/harshitboots/ScreenSight/tree/main/examples).

---

## Claude Code

=== "Project-level (recommended)"

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

=== "Global"

    Add to `~/.claude.json`:

    ```json
    {
      "mcpServers": {
        "screensight": {
          "command": "screensight-mcp"
        }
      }
    }
    ```

=== "Legacy skill adapter"

    ```bash
    bash install.sh --with-claude-skill
    ```

    Copies the legacy skill to `~/.claude/skills/SKILL.md`. Optional — the MCP server is
    the supported path.

## Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

Restart Cursor after saving.

## Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

Restart Windsurf after saving.

## Cline

Add to VS Code `settings.json`:

```json
{
  "cline.mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

Restart VS Code after saving.

## Codex CLI

Add the same `mcpServers` block to `~/.codex/config.json`.

## Aider and other non-MCP agents

No configuration is needed — the agent shells out to the CLI. Put this in your agent
instructions or system prompt:

```text
When I ask you to look at my screen, run:
  screensight capture

The output will contain a "path" field with the screenshot location.
Read that file to see what's on my screen.
```

---

!!! note "The switch still applies"
    Wiring up an agent does not enable capture. The master switch is off until you run
    `screensight on` — or until the agent calls `screen_enable` and you allow it.

## Verify the connection

Ask the agent *"what's on my screen?"*. It should call `screen_capture` and describe the
frame. If the tool doesn't appear at all:

```bash
which screensight-mcp    # Linux / macOS
where screensight-mcp    # Windows
```

If the binary isn't found, the agent can't spawn it — reinstall with `pip install -e .`
or use an absolute path in the `command` field. More in
[Troubleshooting](../help/troubleshooting.md).
