<!--
  Thanks for contributing to ScreenSight! Please read CONTRIBUTING.md first.
  Keep the change focused and preserve the six privacy invariants.
-->

## What does this PR do?

<!-- A short description of the change and why. Link any related issue: Closes #123 -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Capture backend change (macOS / Linux / Windows)
- [ ] Docs / examples
- [ ] Tests / tooling

## Testing

- [ ] `pytest tests/ -v` passes locally
- [ ] I added or updated tests for this change

**Platform(s) I actually ran this on:**
<!-- e.g. "Windows 11 / Python 3.11". Be honest about what you did NOT test —
     untested is fine, undisclosed is not. -->

## Privacy invariants (see CONTRIBUTING.md / PROJECT.md)

- [ ] Every capture path still routes through `core.capture_once()` — no backend called directly outside `core.py`
- [ ] The master-switch check remains the single source of truth in `core.py`
- [ ] Blocklist / redaction logic is unchanged, or strictly *more* conservative (and noted in PROJECT.md)
- [ ] No new screenshot files accumulate on disk; cleanup on `off` still holds
- [ ] Cross-platform parity: backend features have an equivalent or documented fallback on all three OSes
- [ ] No new runtime dependencies (beyond `fastmcp`, `pillow`), or the PR explains why one is needed

## Notes for reviewers

<!-- Anything non-obvious, trade-offs, follow-ups. -->
