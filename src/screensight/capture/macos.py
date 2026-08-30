from __future__ import annotations

import subprocess

from .base import CaptureBackend, CaptureResult


class MacOSCapture(CaptureBackend):
    def screenshot(self, out_path: str, display: int | None = None) -> CaptureResult:
        cmd = ["screencapture", "-x", "-t", "jpg"]
        if display is not None:
            cmd += ["-D", str(display + 1)]  # screencapture displays are 1-indexed
        cmd.append(out_path)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)
            if proc.returncode != 0:
                return CaptureResult(ok=False, error=proc.stderr.strip() or "screencapture failed")
            return CaptureResult(
                ok=True, path=out_path, active_window_title=self.active_window_title()
            )
        except FileNotFoundError:
            return CaptureResult(ok=False, error="screencapture not found (unexpected on macOS)")
        except subprocess.TimeoutExpired:
            return CaptureResult(
                ok=False, error="screencapture timed out — check Screen Recording permission"
            )

    def active_window_title(self) -> str | None:
        script = (
            'tell application "System Events" to get name of first application process '
            "whose frontmost is true"
        )
        try:
            proc = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=5, check=False
            )
            if proc.returncode == 0:
                return proc.stdout.strip() or None
        except Exception:
            pass
        return None

    def list_displays(self) -> list[dict]:
        try:
            proc = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            import json

            data = json.loads(proc.stdout)
            displays = []
            for gpu in data.get("SPDisplaysDataType", []):
                for i, d in enumerate(gpu.get("spdisplays_ndrvs", [])):
                    displays.append({"index": i, "name": d.get("_name", f"display-{i}")})
            return displays or [{"index": 0, "name": "primary"}]
        except Exception:
            return [{"index": 0, "name": "primary"}]
