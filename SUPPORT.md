# Support

Thanks for using ScreenSight! Here's how to get help.

## Before opening an issue

Most problems are covered in the docs:

- **[GUIDE.md → Troubleshooting](GUIDE.md#troubleshooting)** — "capture failed: off",
  blocklist matches, PowerShell capture failures, "daemon already running", MCP
  server not starting, and more.
- **[README.md](README.md)** — install, per-agent MCP config, CLI usage, privacy model.

Quick self-checks:

```bash
screensight status        # is the master switch on?
screensight --help        # CLI options
which screensight-mcp      # (Windows: where screensight-mcp) is the server installed?
```

Logs, if enabled, are at `~/.screensight/screensight.log`.

## Asking a question

- **Usage questions / "how do I…"** — open a
  [GitHub Discussion](https://github.com/himanshu231204/ScreenSight/discussions)
  (or an issue if Discussions aren't enabled yet).
- **Agent-specific setup** (Cursor, Windsurf, Cline, Codex, Aider, etc.) — check the
  ready-made config snippets in [`examples/`](examples/) first.

## Reporting a bug

Open a [bug report](https://github.com/himanshu231204/ScreenSight/issues/new/choose)
and include:

- Your **OS** (Windows / macOS / Linux / WSL) and **Python version**
- ScreenSight version (`0.1.0`) or commit
- The exact command and its full output
- What you expected vs. what happened

Note that macOS, Linux, and WSL backends are currently marked ⚠️ untested — bug
reports (and confirmations that they *work*) on those platforms are especially
welcome.

## Requesting a feature

Open a [feature request](https://github.com/himanshu231204/ScreenSight/issues/new/choose).
Please check [`PROJECT.md` → "Explicitly out of scope for v1"](PROJECT.md) first —
things like OCR-based sensitive-content detection and a GUI settings app are
intentionally deferred.

## Security issues

**Do not** report security vulnerabilities in public issues. See
[SECURITY.md](SECURITY.md) for private reporting.
