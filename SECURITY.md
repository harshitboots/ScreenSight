# Security Policy

ScreenSight captures screen contents, so security and privacy are core to the
project rather than an afterthought. Please treat any weakening of the privacy
guarantees below as a security issue.

## Supported versions

ScreenSight is pre-1.0. Security fixes are applied to the latest released version
(currently `0.1.0`) and `main`.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |
| < 0.1   | ❌        |

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report privately using one of:

- GitHub's [private vulnerability reporting](https://github.com/himanshu231204/ScreenSight/security/advisories/new)
  (Security → Report a vulnerability)
- Email: **himanshu231204@gmail.com**

Please include:

- A description of the issue and its impact
- Steps to reproduce (or a proof of concept)
- Affected version / commit
- Your platform (OS + Python version)

You can expect an acknowledgement within a few days. Once fixed, we'll credit you
in the release notes unless you'd prefer to remain anonymous.

## What counts as a security issue here

Because of what this tool does, the following are treated as security-severity
bugs, not ordinary bugs:

- **Capture while the master switch is off.** Any code path that produces a frame
  without `core.capture_once()`'s switch check passing.
- **Blocklist bypass.** A sensitive window (password manager, incognito, etc.)
  whose title matches the blocklist but a frame is still saved.
- **Redaction bypass.** A configured redact zone that is not blacked out before the
  frame is written to disk.
- **Frame leakage.** Frames written outside `~/.screensight/`, not overwritten, or
  not deleted on `screensight off`.
- **Prompt-injection bypass.** Any way for an instruction (in a tool description,
  captured screen text, or agent prompt) to cause a capture that the switch/
  blocklist would otherwise refuse.

## Design safeguards (context for reviewers)

These are the mechanisms an attacker would have to defeat — see `PROJECT.md` and
`ARCHITECTURE.md` for detail:

- The master-switch check is inside `core.capture_once()`, the single capture
  choke point — not in a prompt or tool description, so it can't be talked around.
- The active-window title is checked against a blocklist *before* a frame is saved.
  A `None` (unknown) title is treated as **not verified safe**.
- User-defined redaction zones are blacked out before the frame leaves disk.
- Exactly one frame file exists at a time; it is overwritten each capture and
  deleted on `off`.

## Scope

ScreenSight has **no network component** and requires no API key — captured frames
never leave your machine except when your own agent reads the local frame file.
Vulnerabilities in third-party agents that consume ScreenSight's output are out of
scope; report those to the respective projects.
