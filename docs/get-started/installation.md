# Installation

ScreenSight requires **Python 3.10+**. Installing it puts two commands on your PATH:

- `screensight` — the CLI
- `screensight-mcp` — the MCP server (stdio)

## Install

=== "From source (recommended)"

    ```bash
    git clone https://github.com/harshitboots/ScreenSight screensight
    cd screensight

    # Linux / macOS
    bash install.sh

    # Windows
    .\install.ps1
    ```

    The installer script also prints an MCP config snippet for your agent.

=== "pip"

    ```bash
    git clone https://github.com/harshitboots/ScreenSight screensight
    cd screensight
    pip install .
    ```

=== "pipx (isolated)"

    ```bash
    pipx install .
    ```

    Use this when you want ScreenSight's dependencies (`fastmcp`, `pillow`) kept out of
    your project environments.

## Verify

```bash
screensight --help
screensight-mcp --help
```

If the shell can't find either command, the install directory isn't on your PATH:

```bash
which screensight      # Linux / macOS
where screensight      # Windows
```

## Claude Code skill adapter (optional)

If you also want the legacy Claude Code skill installed alongside the MCP server:

```bash
bash install.sh --with-claude-skill
```

This copies the skill to `~/.claude/skills/SKILL.md`. It is not required — the MCP server
is the supported path.

## Uninstall

```bash
pip uninstall screensight     # or: pipx uninstall screensight
rm -rf ~/.screensight         # removes the switch, frame and config
```

Removing `~/.screensight` deletes the current frame, the master switch state, and your
blocklist and redaction zone customizations.

## Next

Head to the [Quickstart](quickstart.md) for your first capture, or straight to
[Agent setup](agent-setup.md) to wire ScreenSight into your editor.
