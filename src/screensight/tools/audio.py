from __future__ import annotations

import base64
from pathlib import Path

from fastmcp import FastMCP

try:  # Audio helper added in newer FastMCP; fall back to a raw resource block if absent.
    from fastmcp.utilities.types import Audio as _Audio
except ImportError:  # pragma: no cover - depends on installed FastMCP version
    _Audio = None  # type: ignore[assignment,misc]

from screensight import core


def screen_capture_audio(
    duration: int = 5,
    question: str = "",
) -> list:
    """Record the system's audio output (what's playing through the speakers).

    Captures loopback audio — the sound the user is hearing (music, a video,
    a call) — for `duration` seconds and returns it as an audio content block
    you can listen to, plus text context.

    This is separate from screen_capture: audio is time-based, so this call
    blocks for roughly `duration` seconds while recording.

    Two gates must be satisfied:
    - The master switch must be ON (screen_enable).
    - Audio must be enabled by the user via the SCREENSIGHT_ENABLE_AUDIO=1
      environment variable — it is OFF by default for privacy.

    Platform notes: Windows (WASAPI) and Linux (PulseAudio monitor) work out of
    the box; macOS and WSL require a virtual loopback device (BlackHole /
    SoundFlower) set as the default output.

    Args:
        duration: Seconds of audio to record (1–30, default 5).
        question: Optional question to echo back for your context.

    Returns:
        Audio content block + text context (+ echoed question if given).
    """
    outcome = core.capture_audio(duration=duration)
    if not outcome.ok:
        return [f"Audio capture failed: {outcome.error}"]

    result_parts: list = []

    audio_path = Path(outcome.path)
    audio_bytes = audio_path.read_bytes()
    if _Audio is not None:
        result_parts.append(_Audio(data=audio_bytes, format="wav"))
    else:
        # Fallback for FastMCP builds without the Audio helper: embed as a
        # base64 audio resource block.
        result_parts.append(
            {
                "type": "audio",
                "data": base64.b64encode(audio_bytes).decode("ascii"),
                "mimeType": "audio/wav",
            }
        )

    text_parts = [
        f"Recorded {outcome.duration}s of system audio at {outcome.sample_rate} Hz",
        f"Audio saved to: {outcome.path}",
    ]
    if question:
        text_parts.append(f"Your question: {question}")
    result_parts.append("\n".join(text_parts))

    return result_parts


def register(mcp: FastMCP) -> None:
    mcp.tool(output_schema=None)(screen_capture_audio)
