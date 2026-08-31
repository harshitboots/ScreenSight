"""System-audio (loopback) capture — the audio counterpart to the screenshot
backends. Kept in its own module because audio is time-based (a duration),
not instantaneous like a screenshot, and because its dependencies
(``soundcard``, ``numpy``) are optional extras that the core screenshot path
must never import.

Platform support via ``soundcard``:
- Windows: WASAPI loopback works out of the box (records the default speaker).
- Linux:   PulseAudio/PipeWire monitor source works out of the box.
- macOS / WSL: there is no OS loopback device; a virtual one
  (BlackHole, SoundFlower) must be installed and selected as the default
  output, otherwise no loopback microphone exists and capture fails with an
  actionable error.

Every failure path returns ``AudioResult(ok=False, error=...)`` — capture must
degrade gracefully rather than raise, matching the rest of the package.
"""

from __future__ import annotations

import wave
from dataclasses import dataclass

_DEPS_HINT = "audio deps not installed — run: pip install 'screensight[audio]'"
_NO_LOOPBACK_HINT = (
    "no loopback audio device found — on macOS/WSL install a virtual output "
    "device (BlackHole or SoundFlower) and set it as the default output"
)


@dataclass
class AudioResult:
    ok: bool
    path: str | None = None
    error: str | None = None
    duration: float | None = None
    sample_rate: int | None = None
    channels: int | None = None


def record_system_audio(out_path: str, duration: float, sample_rate: int) -> AudioResult:
    """Record ``duration`` seconds of system audio output to ``out_path`` as a
    16-bit PCM WAV. Returns an :class:`AudioResult`; never raises."""
    try:
        import numpy as np
        import soundcard as sc  # type: ignore[import-untyped]
    except ImportError:
        return AudioResult(ok=False, error=_DEPS_HINT)

    try:
        speaker = sc.default_speaker()
        if speaker is None:
            return AudioResult(ok=False, error=_NO_LOOPBACK_HINT)

        # include_loopback=True returns a microphone that records the speaker's
        # output rather than a physical input.
        loopback = sc.get_microphone(speaker.name, include_loopback=True)
        if loopback is None:
            return AudioResult(ok=False, error=_NO_LOOPBACK_HINT)

        frames = int(duration * sample_rate)
        with loopback.recorder(samplerate=sample_rate) as rec:
            data = rec.record(numframes=frames)  # float32 array, shape (frames, channels)

        channels = data.shape[1] if data.ndim > 1 else 1

        # Convert float32 [-1.0, 1.0] to int16 PCM, clipping out-of-range values.
        clipped = np.clip(data, -1.0, 1.0)
        pcm16 = (clipped * 32767).astype("<i2")

        with wave.open(out_path, "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            wav.writeframes(pcm16.tobytes())

        return AudioResult(
            ok=True,
            path=out_path,
            duration=float(duration),
            sample_rate=sample_rate,
            channels=channels,
        )
    except Exception as e:  # capture must fail closed, never raise
        return AudioResult(ok=False, error=f"audio capture failed: {e}")
