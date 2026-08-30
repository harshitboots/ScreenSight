---
title: ScreenSight
hide:
  - navigation
  - toc
---

<div class="ss-hero" markdown>

<span class="ss-hero__eyebrow">MCP server · CLI · Watch daemon</span>

# Let *any* coding agent see your screen { .ss-hero__title }

<p class="ss-hero__subtitle">
ScreenSight is a privacy-first screen capture layer for coding agents. It ships as an MCP
server for Cursor, Windsurf, Cline, Claude Code and Codex CLI, a plain CLI for everything
else, and a bounded watch daemon for capture over time. No API key. Off by default.
</p>

<div class="ss-hero__actions" markdown>
[Get started](get-started/quickstart.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/harshitboots/ScreenSight){ .md-button }
</div>

<div class="ss-hero__code" markdown>

```bash
pip install .
screensight on
screensight capture
```

</div>

</div>

## Start here

<div class="ss-grid" markdown>

<a class="ss-card" href="get-started/installation/">
<span class="ss-card__title">:material-download: Installation</span>
<span class="ss-card__body">Install from source, with pip, or with pipx. Python 3.10+ on Windows, macOS, Linux and WSL.</span>
<span class="ss-card__meta">Install →</span>
</a>

<a class="ss-card" href="get-started/quickstart/">
<span class="ss-card__title">:material-rocket-launch: Quickstart</span>
<span class="ss-card__body">Enable the switch, take your first capture, and confirm your agent can see the frame — about two minutes.</span>
<span class="ss-card__meta">Two-minute tour →</span>
</a>

<a class="ss-card" href="get-started/agent-setup/">
<span class="ss-card__title">:material-robot-outline: Agent setup</span>
<span class="ss-card__body">Copy-paste MCP config for Claude Code, Cursor, Windsurf, Cline, Codex CLI — plus the CLI path for Aider.</span>
<span class="ss-card__meta">Wire up your agent →</span>
</a>

<a class="ss-card" href="reference/mcp-tools/">
<span class="ss-card__title">:material-toolbox-outline: MCP tools</span>
<span class="ss-card__body">All eight tools the server exposes, with inputs, outputs and example responses.</span>
<span class="ss-card__meta">Read the reference →</span>
</a>

<a class="ss-card" href="reference/cli/">
<span class="ss-card__title">:material-console: CLI reference</span>
<span class="ss-card__body">Every command, flag, JSON payload and exit code for the <code>screensight</code> binary.</span>
<span class="ss-card__meta">Browse commands →</span>
</a>

<a class="ss-card" href="privacy/">
<span class="ss-card__title">:material-shield-lock-outline: Privacy model</span>
<span class="ss-card__body">Master switch, sensitive-app blocklist, zone redaction, frame hygiene and watch self-limits.</span>
<span class="ss-card__meta">See the guarantees →</span>
</a>

</div>

## Why ScreenSight

<div class="ss-features" markdown>

<div markdown>
<p class="ss-feature__title">Agent-agnostic by construction</p>
<p class="ss-feature__body">One MCP server works in every MCP-capable agent with zero agent-specific code. Agents without MCP shell out to the CLI instead.</p>
</div>

<div markdown>
<p class="ss-feature__title">Off unless you say otherwise</p>
<p class="ss-feature__body">A master switch gates every capture, and the check lives inside the capture pipeline — not in a tool description an injected instruction could argue with.</p>
</div>

<div markdown>
<p class="ss-feature__title">Sensitive windows never land on disk</p>
<p class="ss-feature__body">Password managers, keychains and incognito windows are matched by title and abort the capture before a frame is written.</p>
</div>

<div markdown>
<p class="ss-feature__title">One frame, not a shoebox of screenshots</p>
<p class="ss-feature__body">A single <code>frame.jpg</code> is overwritten on every capture and deleted when you turn the switch off.</p>
</div>

<div markdown>
<p class="ss-feature__title">Bounded watching</p>
<p class="ss-feature__body">The watch daemon stops itself after a frame budget and flips the master switch off on exit, so an idle daemon can't quietly keep burning tokens.</p>
</div>

<div markdown>
<p class="ss-feature__title">Cheap frames</p>
<p class="ss-feature__body">Every image is downscaled to a 1568px long edge — past the point extra pixels help a vision model — keeping token cost low for every consumer.</p>
</div>

</div>

## How it compares

| Feature | ScreenSight | ScreenPipe | Agent-specific tools |
|---------|:-----------:|:----------:|:--------------------:|
| Works with any MCP agent | ✅ | ❌ | ❌ |
| CLI fallback (no MCP needed) | ✅ | ❌ | Varies |
| Watch daemon with auto-stop | ✅ | ✅ | ❌ |
| Master switch (off by default) | ✅ | ❌ | Varies |
| Blocklist + zone redaction | ✅ | ❌ | ❌ |
| No API key required | ✅ | ✅ | Varies |
| Cross-platform | ✅ | ✅ | Varies |
| 1568px downscale for tokens | ✅ | ❌ | ❌ |
| Frame cleanup on off | ✅ | ❌ | ❌ |
| Open source | ✅ | ✅ | Varies |

Inspired by [ScreenPipe](https://github.com/mediar-ai/screenpipe) — this is the agent-agnostic version.
