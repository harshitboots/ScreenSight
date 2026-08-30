"""Tests for WSL capture backend with mocked subprocess calls."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from screensight.capture.base import CaptureBackend, CaptureResult
from screensight.capture.windows import (
    WSLCapture,
    WindowsCapture,
    get_windows_temp_dir,
    is_wsl2,
    win_to_wsl_path,
    wsl_to_win_path,
)


def _write_real_jpeg(path: Path) -> None:
    """Write a minimal but valid JPEG file that PIL can open."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="blue")
    img.save(str(path), "JPEG")


def _mock_subprocess_run(responses: dict):
    """Create a mock for subprocess.run that returns predefined responses.
    
    Args:
        responses: dict mapping command prefixes to (returncode, stdout, stderr) tuples
    """
    def mock_run(cmd, *args, **kwargs):
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        for prefix, (returncode, stdout, stderr) in responses.items():
            if prefix in cmd_str:
                result = MagicMock()
                result.returncode = returncode
                result.stdout = stdout
                result.stderr = stderr
                return result
        # Default: command not found
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = f"Command not found: {cmd_str}"
        return result
    
    return mock_run


# ============================================================================
# Path Translation Helpers
# ============================================================================


class TestWinToWslPath:
    """Test win_to_wsl_path() function."""

    def test_success(self, monkeypatch):
        """Convert Windows path to WSL path."""
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "wslpath -u": (0, "/mnt/c/Users/test/temp", ""),
            }),
        )
        monkeypatch.setattr(
            "shutil.which",
            lambda x: "wslpath" if x == "wslpath" else None,
        )
        result = win_to_wsl_path("C:\\Users\\test\\temp")
        assert result == "/mnt/c/Users/test/temp"

    def test_wslpath_not_found(self, monkeypatch):
        """Error when wslpath is not installed."""
        monkeypatch.setattr(
            "shutil.which",
            lambda x: None,
        )
        with pytest.raises(RuntimeError, match="wslpath not found"):
            win_to_wsl_path("C:\\Users\\test\\temp")

    def test_conversion_failure(self, monkeypatch):
        """Error when wslpath conversion fails."""
        monkeypatch.setattr(
            "shutil.which",
            lambda x: "wslpath" if x == "wslpath" else None,
        )
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "wslpath -u": (1, "", "invalid path"),
            }),
        )
        with pytest.raises(RuntimeError, match="wslpath failed"):
            win_to_wsl_path("invalid\\path")


class TestWslToWinPath:
    """Test wsl_to_win_path() function."""

    def test_success(self, monkeypatch):
        """Convert WSL path to Windows path."""
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "wslpath -w": (0, "C:\\Users\\test\\temp", ""),
            }),
        )
        monkeypatch.setattr(
            "shutil.which",
            lambda x: "wslpath" if x == "wslpath" else None,
        )
        result = wsl_to_win_path("/mnt/c/Users/test/temp")
        assert result == "C:\\Users\\test\\temp"

    def test_wslpath_not_found(self, monkeypatch):
        """Error when wslpath is not installed."""
        monkeypatch.setattr(
            "shutil.which",
            lambda x: None,
        )
        with pytest.raises(RuntimeError, match="wslpath not found"):
            wsl_to_win_path("/mnt/c/Users/test/temp")


class TestGetWindowsTempDir:
    """Test get_windows_temp_dir() function."""

    def test_success(self, monkeypatch):
        """Get Windows TEMP directory."""
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "powershell.exe": (0, "C:\\Users\\test\\AppData\\Local\\Temp", ""),
            }),
        )
        result = get_windows_temp_dir()
        assert result == "C:\\Users\\test\\AppData\\Local\\Temp"

    def test_powershell_failure(self, monkeypatch):
        """Error when PowerShell fails."""
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "powershell.exe": (1, "", "access denied"),
            }),
        )
        with pytest.raises(RuntimeError, match="Failed to get Windows TEMP dir"):
            get_windows_temp_dir()


# ============================================================================
# WSL Environment Detection
# ============================================================================


class TestIsWsl2:
    """Test is_wsl2() function."""

    def test_wsl2_detected(self, monkeypatch):
        """Detect WSL2 from wsl.exe output."""
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "wsl.exe": (0, "  Ubuntu    Running    2", ""),
            }),
        )
        assert is_wsl2() is True

    def test_wsl1_detected(self, monkeypatch):
        """Detect WSL1 from wsl.exe output."""
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "wsl.exe": (0, "  Ubuntu    Running    1", ""),
            }),
        )
        assert is_wsl2() is False

    def test_assume_wsl2_on_error(self, monkeypatch):
        """Assume WSL2 when wsl.exe fails."""
        def failing_run(cmd, *args, **kwargs):
            raise Exception("wsl.exe not found")
        
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            failing_run,
        )
        assert is_wsl2() is True


# ============================================================================
# WSLCapture Class
# ============================================================================


class TestWSLCapture:
    """Test WSLCapture class."""

    def test_screenshot_success(self, tmp_path, monkeypatch):
        """Successful capture from WSL."""
        out_path = str(tmp_path / "frame.jpg")
        win_temp = "C:\\Users\\test\\AppData\\Local\\Temp"
        win_out = f"{win_temp}\\screensight-frame.jpg"
        wsl_out = "/mnt/c/Users/test/AppData/Local/Temp/screensight-frame.jpg"

        # Mock subprocess calls
        responses = {
            "powershell.exe $env:TEMP": (0, win_temp, ""),
            "powershell.exe": (0, "Test Window", ""),
            "wslpath -u": (0, wsl_out, ""),
        }
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run(responses),
        )
        # Patch shutil.which in the windows module
        import screensight.capture.windows as win_module
        original_which = win_module.shutil.which
        win_module.shutil.which = lambda x: "powershell.exe" if x == "powershell.exe" else None

        # Create the WSL path file (simulating Windows capture)
        Path(wsl_out).parent.mkdir(parents=True, exist_ok=True)
        _write_real_jpeg(Path(wsl_out))

        capture = WSLCapture()
        result = capture.screenshot(out_path)

        # Restore original
        win_module.shutil.which = original_which

        assert result.ok is True
        assert result.path == out_path
        assert result.active_window_title == "Test Window"
        assert Path(out_path).exists()
        # Windows temp file should be cleaned up
        assert not Path(wsl_out).exists()

    def test_screenshot_powershell_not_found(self, monkeypatch):
        """Error when powershell.exe is not found."""
        monkeypatch.setattr(
            "shutil.which",
            lambda x: None,
        )
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({}),
        )

        capture = WSLCapture()
        result = capture.screenshot("/tmp/frame.jpg")

        assert result.ok is False
        assert "powershell.exe not found" in result.error

    def test_screenshot_temp_dir_failure(self, monkeypatch):
        """Error when Windows TEMP dir cannot be obtained."""
        monkeypatch.setattr(
            "shutil.which",
            lambda x: "powershell.exe" if x == "powershell.exe" else None,
        )
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "powershell.exe": (1, "", "access denied"),
            }),
        )

        capture = WSLCapture()
        result = capture.screenshot("/tmp/frame.jpg")

        assert result.ok is False
        assert "Failed to get Windows TEMP dir" in result.error

    def test_screenshot_path_translation_failure(self, tmp_path, monkeypatch):
        """Error when path translation fails."""
        out_path = str(tmp_path / "frame.jpg")
        win_temp = str(tmp_path / "win_temp")
        win_out = f"{win_temp}\\screensight-frame.jpg"

        # Create the Windows path file in tmp_path
        Path(win_temp).mkdir(parents=True, exist_ok=True)
        _write_real_jpeg(Path(win_out))

        # Mock successful capture but failed path translation
        responses = {
            "powershell.exe $env:TEMP": (0, win_temp, ""),
            "powershell.exe": (0, "Test Window", ""),
            "wslpath -u": (1, "", "invalid path"),
        }
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run(responses),
        )
        monkeypatch.setattr(
            "shutil.which",
            lambda x: "powershell.exe" if x == "powershell.exe" else None,
        )

        capture = WSLCapture()
        result = capture.screenshot(out_path)

        assert result.ok is False
        assert "Path translation failed" in result.error

    def test_screenshot_file_not_found_after_capture(self, tmp_path, monkeypatch):
        """Error when captured file is not found at WSL path."""
        out_path = str(tmp_path / "frame.jpg")
        win_temp = str(tmp_path / "win_temp")
        win_out = f"{win_temp}\\screensight-frame.jpg"
        wsl_out = "/mnt/c/Users/test/AppData/Local/Temp/screensight-frame.jpg"

        # Create the Windows path file
        Path(win_temp).mkdir(parents=True, exist_ok=True)
        _write_real_jpeg(Path(win_out))

        # Mock successful capture and path translation, but file doesn't exist at wsl_out
        responses = {
            "powershell.exe $env:TEMP": (0, win_temp, ""),
            "powershell.exe": (0, "Test Window", ""),
            "wslpath -u": (0, wsl_out, ""),
        }
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run(responses),
        )
        # Patch shutil.which in the windows module
        import screensight.capture.windows as win_module
        original_which = win_module.shutil.which
        win_module.shutil.which = lambda x: "powershell.exe" if x == "powershell.exe" else None

        capture = WSLCapture()
        result = capture.screenshot(out_path)

        # Restore original
        win_module.shutil.which = original_which

        assert result.ok is False
        assert "Captured file not found at WSL path" in result.error

    def test_active_window_title_success(self, monkeypatch):
        """Get active window title from WSL."""
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "powershell.exe": (0, "VS Code", ""),
            }),
        )

        capture = WSLCapture()
        title = capture.active_window_title()
        assert title == "VS Code"

    def test_active_window_title_fallback(self, monkeypatch):
        """Fallback to None when title extraction fails."""
        def failing_run(cmd, *args, **kwargs):
            raise Exception("PowerShell failed")
        
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            failing_run,
        )

        capture = WSLCapture()
        title = capture.active_window_title()
        assert title is None

    def test_list_displays_success(self, monkeypatch):
        """List displays from WSL."""
        # PowerShell output uses backslashes which get escaped in Python strings
        display_output = "0|\\\\.\\DISPLAY1|1920x1080\n1|\\\\.\\DISPLAY2|2560x1440"
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            _mock_subprocess_run({
                "powershell.exe": (0, display_output, ""),
            }),
        )

        capture = WSLCapture()
        displays = capture.list_displays()
        
        assert len(displays) == 2
        assert displays[0]["index"] == 0
        # The name will be stripped of leading backslashes by .strip("\\")
        assert displays[0]["name"] == ".\\DISPLAY1"
        assert displays[0]["resolution"] == "1920x1080"
        assert displays[1]["index"] == 1
        assert displays[1]["resolution"] == "2560x1440"

    def test_list_displays_fallback(self, monkeypatch):
        """Fallback to primary display when listing fails."""
        def failing_run(cmd, *args, **kwargs):
            raise Exception("PowerShell failed")
        
        monkeypatch.setattr(
            "screensight.capture.windows.subprocess.run",
            failing_run,
        )

        capture = WSLCapture()
        displays = capture.list_displays()
        
        assert displays == [{"index": 0, "name": "primary"}]


# ============================================================================
# Integration with core.py
# ============================================================================


class TestWSLBackendDispatch:
    """Test that WSL backend is correctly dispatched."""

    def test_get_backend_returns_wsl_capture(self, monkeypatch):
        """Verify get_backend() returns WSLCapture when OS is WSL."""
        from screensight.capture.base import get_backend

        monkeypatch.setattr("screensight.config.get_os", lambda: "wsl")
        
        backend = get_backend()
        assert isinstance(backend, WSLCapture)

    def test_wsl_capture_inherits_from_windows(self):
        """Verify WSLCapture inherits from WindowsCapture."""
        assert issubclass(WSLCapture, WindowsCapture)

    def test_wsl_capture_implements_backend(self):
        """Verify WSLCapture implements CaptureBackend."""
        assert issubclass(WSLCapture, CaptureBackend)
