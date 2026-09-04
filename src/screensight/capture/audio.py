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

import shutil
import struct
import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

_DEPS_HINT = "audio deps not installed — run: pip install 'screensight[audio]'"
_NO_LOOPBACK_HINT = (
    "no loopback audio device found — on macOS/WSL install a virtual output "
    "device (BlackHole or SoundFlower) and set it as the default output"
)
_POCKETSTATION_HINT = (
    "PocketStation is not installed — run: pip install 'screensight[pocketstation]'"
)
_POCKETSTATION_SAMPLE_RATE = 48_000


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


def record_pocketstation_audio(
    out_path: str,
    duration: float,
    source: str,
    application: str | None = None,
) -> AudioResult:
    """Record one application or the default microphone with PocketStation."""
    try:
        import pocketstation
    except ImportError:
        return AudioResult(ok=False, error=_POCKETSTATION_HINT)

    try:
        declaration = _pocketstation_source(pocketstation, source, application)
        with tempfile.TemporaryDirectory(prefix="screensight-audio-") as directory:
            session = pocketstation.Session(
                recording_root=directory,
                sample_rate_hz=_POCKETSTATION_SAMPLE_RATE,
                channels=1,
            )
            stem = session.capture(declaration)
            stem.record(source)
            running = session.start()
            try:
                time.sleep(duration)
                result = running.stop()
            finally:
                running.close()

            recording = result.recording
            if recording is None or not recording.complete:
                return AudioResult(
                    ok=False,
                    error="PocketStation could not finish the audio recording",
                )

            captured = Path(recording.session_directory) / "stems" / f"{source}.wav"
            if not captured.is_file():
                return AudioResult(
                    ok=False,
                    error=f"PocketStation did not create the {source} recording",
                )
            shutil.copyfile(captured, out_path)

        sample_rate, channels = _read_wave_format(out_path)
        return AudioResult(
            ok=True,
            path=out_path,
            duration=float(duration),
            sample_rate=sample_rate,
            channels=channels,
        )
    except Exception as error:  # capture must fail closed, never raise
        return AudioResult(ok=False, error=f"PocketStation audio capture failed: {error}")


def _pocketstation_source(
    pocketstation: ModuleType,
    source: str,
    application: str | None,
) -> Any:
    if source == "microphone":
        return pocketstation.Source.microphone_default()
    if source != "application":
        raise ValueError("PocketStation source must be 'application' or 'microphone'")

    selected = "" if application is None else application.strip()
    if not selected:
        raise ValueError("application is required when source is 'application'")
    process_id = selected.removeprefix("pid:")
    if process_id != selected:
        if not process_id.isascii() or not process_id.isdecimal() or int(process_id) <= 0:
            raise ValueError("application process IDs must use pid:<positive integer>")
        return pocketstation.Source.application_process_id(int(process_id))
    if selected.startswith("bundle:"):
        bundle_id = selected.removeprefix("bundle:")
        if not bundle_id:
            raise ValueError("bundle: application selectors must not be empty")
        return pocketstation.Source.application_bundle_id(bundle_id)
    return pocketstation.Source.application(selected)


def _read_wave_format(path: str) -> tuple[int, int]:
    """Read sample rate and channel count from PCM or extensible WAV files."""
    with open(path, "rb") as audio:
        if audio.read(4) != b"RIFF":
            raise ValueError("recording is not a RIFF file")
        audio.seek(4, 1)
        if audio.read(4) != b"WAVE":
            raise ValueError("recording is not a WAVE file")
        while header := audio.read(8):
            if len(header) != 8:
                break
            chunk_id, chunk_size = struct.unpack("<4sI", header)
            if chunk_id == b"fmt ":
                payload = audio.read(chunk_size)
                if len(payload) < 8:
                    break
                _, channels, sample_rate = struct.unpack_from("<HHI", payload)
                return sample_rate, channels
            audio.seek(chunk_size + (chunk_size % 2), 1)
    raise ValueError("recording has no valid WAVE format chunk")
