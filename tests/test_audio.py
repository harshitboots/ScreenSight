"""Tests for the capture_audio() pipeline and audio file cleanup, with the
soundcard/numpy hardware path mocked out."""

from __future__ import annotations

import wave
from pathlib import Path

from screensight import core, state
from screensight.capture.audio import AudioResult


def _write_silent_wav(path: Path, duration: float = 1.0, sample_rate: int = 44100) -> None:
    """Write a valid, silent mono 16-bit WAV so no hardware is touched."""
    frames = int(duration * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)


def _mock_record(**overrides):
    """Return a fake record_system_audio that writes a silent WAV and records
    the args it was called with in `calls`."""
    calls: list = []

    def _record(out_path, duration, sample_rate):
        calls.append({"out_path": out_path, "duration": duration, "sample_rate": sample_rate})
        _write_silent_wav(Path(out_path), duration=1.0, sample_rate=sample_rate)
        return AudioResult(
            ok=True,
            path=out_path,
            duration=float(duration),
            sample_rate=sample_rate,
            channels=1,
            **overrides,
        )

    return _record, calls


def test_switch_off_short_circuits(tmp_path, monkeypatch):
    """capture_audio() returns error='off' when the master switch is off,
    without ever recording."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.setenv("SCREENSIGHT_ENABLE_AUDIO", "1")

    record, calls = _mock_record()
    monkeypatch.setattr(core, "record_system_audio", record)

    result = core.capture_audio()
    assert result.ok is False
    assert result.error == "off"
    assert calls == []


def test_disabled_without_env(tmp_path, monkeypatch):
    """With the master switch on but SCREENSIGHT_ENABLE_AUDIO unset, capture is
    refused and nothing is recorded."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.delenv("SCREENSIGHT_ENABLE_AUDIO", raising=False)
    state.turn_on()

    record, calls = _mock_record()
    monkeypatch.setattr(core, "record_system_audio", record)

    result = core.capture_audio()
    assert result.ok is False
    assert "disabled" in result.error
    assert calls == []


def test_successful_capture(tmp_path, monkeypatch):
    """A normal capture returns ok=True with path, duration, and sample rate."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.setenv("SCREENSIGHT_ENABLE_AUDIO", "1")
    state.turn_on()

    record, calls = _mock_record()
    monkeypatch.setattr(core, "record_system_audio", record)

    result = core.capture_audio(duration=3)
    assert result.ok is True
    assert result.path == str(tmp_path / "audio.wav")
    assert result.duration == 3.0
    assert result.sample_rate == core.AUDIO_SAMPLE_RATE
    assert (tmp_path / "audio.wav").exists()
    assert calls[0]["duration"] == 3


def test_duration_is_clamped(tmp_path, monkeypatch):
    """Durations above MAX_AUDIO_DURATION are clamped before recording."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.setenv("SCREENSIGHT_ENABLE_AUDIO", "1")
    state.turn_on()

    record, calls = _mock_record()
    monkeypatch.setattr(core, "record_system_audio", record)

    core.capture_audio(duration=999)
    assert calls[0]["duration"] == core.MAX_AUDIO_DURATION


def test_record_failure_propagates(tmp_path, monkeypatch):
    """A failing recorder surfaces ok=False with the error message."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.setenv("SCREENSIGHT_ENABLE_AUDIO", "1")
    state.turn_on()

    monkeypatch.setattr(
        core,
        "record_system_audio",
        lambda *a, **k: AudioResult(ok=False, error="no loopback device"),
    )

    result = core.capture_audio()
    assert result.ok is False
    assert result.error == "no loopback device"


def test_turn_off_deletes_audio(tmp_path, monkeypatch):
    """state.turn_off() removes the audio file, satisfying the cleanup
    acceptance criterion."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(state, "FRAME_PATH", tmp_path / "frame.jpg")
    monkeypatch.setattr(state, "AUDIO_PATH", tmp_path / "audio.wav")

    _write_silent_wav(tmp_path / "audio.wav")
    assert (tmp_path / "audio.wav").exists()

    state.turn_off()
    assert not (tmp_path / "audio.wav").exists()
