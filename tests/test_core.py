"""Tests for the capture_once() pipeline with mocked backends."""

from __future__ import annotations

from pathlib import Path

from screensight import core, state
from screensight.capture.base import CaptureResult


def _write_real_jpeg(path: Path) -> None:
    """Write a minimal but valid JPEG file that PIL can open."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="blue")
    img.save(str(path), "JPEG")


def _make_mock_backend(ok=True, title="Test Window", error=None):
    """Return a mock CaptureBackend that always succeeds (or always fails)."""
    from screensight.capture.base import CaptureBackend

    class MockBackend(CaptureBackend):
        def screenshot(self, out_path, display=None):
            if not ok:
                return CaptureResult(ok=False, error=error or "mock error")
            _write_real_jpeg(Path(out_path))
            return CaptureResult(ok=True, path=out_path, active_window_title=title)

        def list_displays(self):
            return [{"index": 0, "name": "mock"}]

    return MockBackend()


def test_switch_off_short_circuits(tmp_path, monkeypatch):
    """capture_once() returns ok=False when the master switch is off,
    without ever calling the backend."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "FRAME_PATH", tmp_path / "frame.jpg")

    called = []

    def tracking_backend():
        called.append(True)
        return _make_mock_backend()

    monkeypatch.setattr(core, "get_backend", tracking_backend)

    result = core.capture_once()
    assert result.ok is False
    assert result.error == "off"
    assert called == []  # backend was never called


def test_blocklisted_title_deletes_frame(tmp_path, monkeypatch):
    """When the active window title is blocklisted, the frame file is
    deleted and capture_once returns ok=False."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "FRAME_PATH", tmp_path / "frame.jpg")
    state.turn_on()

    monkeypatch.setattr(
        core,
        "get_backend",
        lambda: _make_mock_backend(title="1Password - Unlock"),
    )

    result = core.capture_once()
    assert result.ok is False
    assert "blocked" in result.error
    assert result.active_window_title == "1Password - Unlock"
    assert not (tmp_path / "frame.jpg").exists()


def test_successful_capture(tmp_path, monkeypatch):
    """A normal capture returns ok=True with path, sha256, and title."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "FRAME_PATH", tmp_path / "frame.jpg")
    state.turn_on()

    monkeypatch.setattr(
        core,
        "get_backend",
        lambda: _make_mock_backend(title="VS Code"),
    )

    result = core.capture_once()
    assert result.ok is True
    assert result.path == str(tmp_path / "frame.jpg")
    assert result.sha256 is not None
    assert result.active_window_title == "VS Code"
    assert (tmp_path / "frame.jpg").exists()


def test_capture_with_display_index(tmp_path, monkeypatch):
    """capture_once() passes the display argument through to the backend."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "FRAME_PATH", tmp_path / "frame.jpg")
    state.turn_on()

    displays = []

    from screensight.capture.base import CaptureBackend

    class TrackingBackend(CaptureBackend):
        def screenshot(self, out_path, display=None):
            displays.append(display)
            _write_real_jpeg(Path(out_path))
            return CaptureResult(ok=True, path=out_path, active_window_title="test")

        def list_displays(self):
            return []

    monkeypatch.setattr(core, "get_backend", lambda: TrackingBackend())

    core.capture_once(display=2)
    assert displays == [2]
