"""Integration proof for PocketStation's returned multistem recording metadata."""

from __future__ import annotations

import json
from array import array
from time import sleep

import pytest

from screensight.capture.audio import _read_wave_format, _recorded_stem_path


@pytest.mark.integration
def test_real_pocketstation_recording_resolves_application_and_microphone_stems(
    tmp_path,
):
    pocketstation = pytest.importorskip("pocketstation")
    session = pocketstation.Session(
        recording_root=tmp_path,
        sample_rate_hz=48_000,
        channels=1,
        frame_duration_ms=10,
    )
    application = session.audio_input(
        "application fixture",
        frame_samples_per_channel=480,
    )
    microphone = session.audio_input(
        "microphone fixture",
        frame_samples_per_channel=480,
    )
    application.output.record("application")
    microphone.output.record("microphone")

    running = session.start()
    samples = array("f", [0.125] * 480)
    try:
        for _ in range(4):
            application.write(samples)
            microphone.write(samples)
            sleep(0.01)
        application.close()
        microphone.close()
        result = running.stop()
    finally:
        running.close()

    assert result.success
    assert result.recording is not None
    assert result.recording.complete
    manifest = json.loads(result.recording.manifest_path.read_text(encoding="utf-8"))
    manifest_stems = {stem["label"]: stem for stem in manifest["stems"]}
    assert set(manifest_stems) == {"application", "microphone"}

    for stem_label in ("application", "microphone"):
        path = _recorded_stem_path(result.recording, stem_label)
        assert (
            path
            == (
                result.recording.session_directory / manifest_stems[stem_label]["wav_path"]
            ).resolve()
        )
        assert path.is_file()
        assert _read_wave_format(str(path)) == (48_000, 1)
