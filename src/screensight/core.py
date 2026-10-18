"""The one function everything else calls. CLI, MCP tools, and the watch
daemon all route through capture_once() so the safety checks live in
exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass

from .capture.audio import record_pocketstation_audio, record_system_audio
from .capture.base import get_backend
from .config import (
    AUDIO_PATH,
    AUDIO_SAMPLE_RATE,
    DEFAULT_AUDIO_DURATION,
    FRAME_PATH,
    MAX_AUDIO_DURATION,
    audio_enabled,
    ensure_base_dir,
)
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


@dataclass
class CaptureAudioOutcome:
    ok: bool
    path: str | None = None
    error: str | None = None
    duration: float | None = None
    sample_rate: int | None = None
    source: str | None = None


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


def capture_audio(
    duration: int | None = None,
    source: str = "system",
    application: str | None = None,
) -> CaptureAudioOutcome:
    """Record system, application, or microphone audio to AUDIO_PATH as a WAV.

    Gated twice: the master switch must be on (same as capture_once) AND audio
    must be explicitly enabled via SCREENSIGHT_ENABLE_AUDIO — audio is never
    recorded by default. Duration is clamped to [1, MAX_AUDIO_DURATION]."""
    if not is_on():
        return CaptureAudioOutcome(ok=False, error="off")
    if not audio_enabled():
        return CaptureAudioOutcome(
            ok=False,
            error="audio capture disabled (set SCREENSIGHT_ENABLE_AUDIO=1 to enable)",
        )

    if duration is None:
        duration = DEFAULT_AUDIO_DURATION
    duration = max(1, min(int(duration), MAX_AUDIO_DURATION))

    source = source.strip().lower()
    if source not in {"system", "application", "microphone"}:
        return CaptureAudioOutcome(
            ok=False,
            error="audio source must be 'system', 'application', or 'microphone'",
        )
    if source == "application" and not (application or "").strip():
        return CaptureAudioOutcome(
            ok=False,
            error="application is required when audio source is 'application'",
        )
    if source != "application" and (application or "").strip():
        return CaptureAudioOutcome(
            ok=False,
            error="application may only be set when audio source is 'application'",
        )

    ensure_base_dir()
    if source == "system":
        result = record_system_audio(str(AUDIO_PATH), duration, AUDIO_SAMPLE_RATE)
    else:
        result = record_pocketstation_audio(
            str(AUDIO_PATH),
            duration,
            source,
            application,
        )
    if not result.ok:
        return CaptureAudioOutcome(ok=False, error=result.error)

    return CaptureAudioOutcome(
        ok=True,
        path=result.path,
        duration=result.duration,
        sample_rate=result.sample_rate,
        source=source,
    )


def list_displays() -> list[dict]:
    return get_backend().list_displays()
