"""Tests for the capture_audio() pipeline and audio file cleanup, with the
soundcard/numpy hardware path mocked out."""

from __future__ import annotations

import builtins
import json
import struct
import sys
import wave
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from screensight import core, state
from screensight.__main__ import cmd_capture_audio
from screensight.__main__ import main as cli_main
from screensight.capture.audio import (
    AudioResult,
    _pocketstation_source,
    _read_wave_format,
    record_pocketstation_audio,
)


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


def _install_fake_pocketstation(
    tmp_path: Path,
    monkeypatch,
    *,
    recording_state: str = "complete",
    create_wav: bool = True,
    declared_path: str | None = None,
) -> list[object]:
    """Install a small API fake while keeping the manifest/path contract real."""
    calls: list[object] = []

    class FakeSource:
        @staticmethod
        def application(name):
            calls.append(("application", name))
            return ("application", name)

        @staticmethod
        def microphone_default():
            calls.append(("microphone",))
            return ("microphone",)

    class FakeStem:
        def __init__(self, session):
            self.session = session

        def record(self, name):
            self.session.stem_label = name
            calls.append(("record", name))

    class FakeRunning:
        def __init__(self, session):
            self.session = session

        def stop(self):
            if recording_state == "none":
                return SimpleNamespace(recording=None)
            root = Path(self.session.recording_root) / "session"
            root.mkdir(parents=True)
            label = self.session.stem_label
            relative_path = declared_path or f"recorded/{label}-capture.wav"
            captured = root / relative_path
            if create_wav:
                captured.parent.mkdir(parents=True, exist_ok=True)
                _write_silent_wav(captured, sample_rate=48000)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "state": recording_state,
                        "stems": [
                            {
                                "label": label,
                                "wav_path": relative_path,
                                "finalization_state": recording_state,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(
                recording=SimpleNamespace(
                    complete=recording_state == "complete",
                    session_directory=root,
                    manifest_path=manifest_path,
                    manifest_schema_version=2,
                )
            )

        def close(self):
            calls.append("close")

    class FakeSession:
        def __init__(self, recording_root, sample_rate_hz):
            self.recording_root = recording_root
            self.stem_label = ""
            calls.append(("format", sample_rate_hz))

        def capture(self, declaration):
            calls.append(("capture", declaration))
            return FakeStem(self)

        def start(self):
            calls.append("start")
            return FakeRunning(self)

    module = ModuleType("pocketstation")
    module.Source = FakeSource
    module.Session = FakeSession
    monkeypatch.setitem(sys.modules, "pocketstation", module)
    monkeypatch.setattr("screensight.capture.audio.time.sleep", lambda _duration: None)
    return calls


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


def test_application_capture_uses_pocketstation_recording(tmp_path, monkeypatch):
    """The adapter follows manifest metadata, not a synthesized stems path."""
    calls = _install_fake_pocketstation(tmp_path, monkeypatch)

    output = tmp_path / "audio.wav"
    result = record_pocketstation_audio(str(output), 2, "application", "Zoom")

    assert result.ok is True
    assert result.sample_rate == 48000
    assert output.is_file()
    assert calls == [
        ("application", "Zoom"),
        ("format", 48000),
        ("capture", ("application", "Zoom")),
        ("record", "application"),
        "start",
        "close",
    ]


def test_microphone_capture_uses_returned_manifest_path(tmp_path, monkeypatch):
    calls = _install_fake_pocketstation(tmp_path, monkeypatch)

    output = tmp_path / "audio.wav"
    result = record_pocketstation_audio(str(output), 2, "microphone")

    assert result.ok is True
    assert result.sample_rate == 48000
    assert output.is_file()
    assert calls == [
        ("microphone",),
        ("format", 48000),
        ("capture", ("microphone",)),
        ("record", "microphone"),
        "start",
        "close",
    ]


def test_pocketstation_import_error_is_actionable(tmp_path, monkeypatch):
    monkeypatch.delitem(sys.modules, "pocketstation", raising=False)
    real_import = builtins.__import__

    def missing_pocketstation(name, *args, **kwargs):
        if name == "pocketstation":
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_pocketstation)

    result = record_pocketstation_audio(str(tmp_path / "audio.wav"), 1, "application", "Zoom")

    assert result.ok is False
    assert result.error == (
        "PocketStation is not installed — run: pip install 'screensight[pocketstation]'"
    )


@pytest.mark.parametrize("recording_state", ["none", "incomplete"])
def test_pocketstation_incomplete_recording_fails_closed(tmp_path, monkeypatch, recording_state):
    _install_fake_pocketstation(
        tmp_path,
        monkeypatch,
        recording_state=recording_state,
    )

    result = record_pocketstation_audio(str(tmp_path / "audio.wav"), 1, "application", "Zoom")

    assert result.ok is False
    assert result.error == "PocketStation could not finish the audio recording"


def test_pocketstation_missing_declared_recording_fails_closed(tmp_path, monkeypatch):
    _install_fake_pocketstation(tmp_path, monkeypatch, create_wav=False)

    result = record_pocketstation_audio(str(tmp_path / "audio.wav"), 1, "application", "Zoom")

    assert result.ok is False
    assert "did not create the declared application recording" in result.error


def test_pocketstation_manifest_cannot_escape_session_directory(tmp_path, monkeypatch):
    outside = tmp_path / "outside.wav"
    _write_silent_wav(outside, sample_rate=48000)
    _install_fake_pocketstation(
        tmp_path,
        monkeypatch,
        create_wav=False,
        declared_path="../outside.wav",
    )

    result = record_pocketstation_audio(str(tmp_path / "audio.wav"), 1, "application", "Zoom")

    assert result.ok is False
    assert "unsafe application recording path" in result.error


def test_pocketstation_selector_supports_name_bundle_process_and_microphone():
    calls: list[tuple] = []
    module = ModuleType("pocketstation")
    module.Source = SimpleNamespace(
        application=lambda value: calls.append(("name", value)) or value,
        application_bundle_id=lambda value: calls.append(("bundle", value)) or value,
        application_process_id=lambda value: calls.append(("pid", value)) or value,
        microphone_default=lambda: calls.append(("microphone",)) or "microphone",
    )

    _pocketstation_source(module, "application", "Zoom")
    _pocketstation_source(module, "application", "bundle:us.zoom.xos")
    _pocketstation_source(module, "application", "pid:123")
    _pocketstation_source(module, "microphone", None)

    assert calls == [
        ("name", "Zoom"),
        ("bundle", "us.zoom.xos"),
        ("pid", 123),
        ("microphone",),
    ]


@pytest.mark.parametrize("selector", ["bundle:", "pid:", "pid:nope", "pid:-1", "pid:0"])
def test_pocketstation_selector_rejects_invalid_values(selector):
    module = ModuleType("pocketstation")
    module.Source = SimpleNamespace()

    with pytest.raises(ValueError):
        _pocketstation_source(module, "application", selector)


def test_application_source_requires_a_selection(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.setenv("SCREENSIGHT_ENABLE_AUDIO", "1")
    state.turn_on()

    result = core.capture_audio(source="application")

    assert result.ok is False
    assert result.error == "application is required when audio source is 'application'"


def test_core_routes_microphone_to_pocketstation(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.setenv("SCREENSIGHT_ENABLE_AUDIO", "1")
    state.turn_on()
    calls: list[tuple] = []

    def record(out_path, duration, source, application):
        calls.append((out_path, duration, source, application))
        return AudioResult(
            ok=True,
            path=out_path,
            duration=float(duration),
            sample_rate=48000,
            channels=1,
        )

    monkeypatch.setattr(core, "record_pocketstation_audio", record)

    result = core.capture_audio(duration=3, source="microphone")

    assert result.ok is True
    assert result.source == "microphone"
    assert result.sample_rate == 48000
    assert calls == [(str(tmp_path / "audio.wav"), 3, "microphone", None)]


def test_core_rejects_application_selector_for_non_application_source(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "AUDIO_PATH", tmp_path / "audio.wav")
    monkeypatch.setenv("SCREENSIGHT_ENABLE_AUDIO", "1")
    state.turn_on()

    result = core.capture_audio(source="microphone", application="Zoom")

    assert result.ok is False
    assert result.error == "application may only be set when audio source is 'application'"


@pytest.mark.parametrize(
    ("source", "application"),
    [("application", None), ("application", " "), ("system", "Zoom"), ("microphone", "Zoom")],
)
def test_cli_reports_audio_usage_errors_with_exit_code_2(source, application, monkeypatch, capsys):
    called = False

    def capture_audio(**_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(core, "capture_audio", capture_audio)
    args = SimpleNamespace(duration=5, source=source, application=application)

    with pytest.raises(SystemExit) as error:
        cmd_capture_audio(args)

    assert error.value.code == 2
    assert called is False
    assert "error" in json.loads(capsys.readouterr().err)


def test_cli_parser_rejects_invalid_audio_source_with_exit_code_2(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["screensight", "capture-audio", "--source", "not-a-source"],
    )

    with pytest.raises(SystemExit) as error:
        cli_main()

    assert error.value.code == 2


def test_cli_reports_capture_failure_with_exit_code_3(monkeypatch, capsys):
    monkeypatch.setattr(
        core,
        "capture_audio",
        lambda **_kwargs: core.CaptureAudioOutcome(ok=False, error="capture backend failed"),
    )
    args = SimpleNamespace(duration=5, source="system", application=None)

    with pytest.raises(SystemExit) as error:
        cmd_capture_audio(args)

    assert error.value.code == 3
    assert json.loads(capsys.readouterr().err) == {"error": "capture backend failed"}


def test_wave_format_reader_accepts_extensible_audio(tmp_path):
    """PocketStation's float WAV header reports its real rate and channels."""
    output = tmp_path / "extensible.wav"
    format_payload = struct.pack(
        "<HHIIHHH",
        0xFFFE,
        2,
        48000,
        384000,
        8,
        32,
        22,
    ) + (b"\x00" * 22)
    riff_size = 4 + 8 + len(format_payload)
    output.write_bytes(
        b"RIFF"
        + struct.pack("<I", riff_size)
        + b"WAVEfmt "
        + struct.pack("<I", len(format_payload))
        + format_payload
    )

    assert _read_wave_format(str(output)) == (48000, 2)


def test_wave_format_reader_accepts_plain_pcm_audio(tmp_path):
    output = tmp_path / "pcm.wav"
    _write_silent_wav(output, sample_rate=44100)

    assert _read_wave_format(str(output)) == (44100, 1)
