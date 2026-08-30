"""The one function everything else calls. CLI, MCP tools, and the watch
daemon all route through capture_once() so the safety checks live in
exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass

from .capture.base import get_backend
from .config import FRAME_PATH, ensure_base_dir
from .diff import sha256_of_file
from .privacy import process_frame, title_is_blocked
from .state import is_on


@dataclass
class CaptureOutcome:
    ok: bool
    path: str | None = None
    sha256: str | None = None
    error: str | None = None
    active_window_title: str | None = None


def capture_once(display: int | None = None) -> CaptureOutcome:
    """Returns exit-code-3 semantics as ok=False, error='off' when the
    master switch is off — checked here, not just in a prompt."""
    if not is_on():
        return CaptureOutcome(ok=False, error="off")

    ensure_base_dir()
    backend = get_backend()
    result = backend.screenshot(str(FRAME_PATH), display=display)
    if not result.ok:
        return CaptureOutcome(ok=False, error=result.error)

    if title_is_blocked(result.active_window_title):
        FRAME_PATH.unlink(missing_ok=True)
        return CaptureOutcome(
            ok=False,
            error=f"blocked: active window '{result.active_window_title}' matches the sensitive-app blocklist",
            active_window_title=result.active_window_title,
        )

    process_frame(str(FRAME_PATH))
    digest = sha256_of_file(str(FRAME_PATH))
    return CaptureOutcome(
        ok=True,
        path=str(FRAME_PATH),
        sha256=digest,
        active_window_title=result.active_window_title,
    )


def list_displays() -> list[dict]:
    return get_backend().list_displays()
