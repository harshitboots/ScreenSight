from __future__ import annotations

import shutil
import subprocess

from .base import CaptureBackend, CaptureResult


class LinuxCapture(CaptureBackend):
    def screenshot(self, out_path: str, display: int | None = None) -> CaptureResult:
        if shutil.which("grim"):
            cmd = ["grim"]
            if display is not None:
                outputs = self._wayland_outputs()
                if display < len(outputs):
                    cmd += ["-o", outputs[display]]
            cmd.append(out_path)
            return self._run(cmd, out_path)

        if shutil.which("gnome-screenshot"):
            return self._run(["gnome-screenshot", "-f", out_path], out_path)

        if shutil.which("import"):  # ImageMagick, X11 only
            return self._run(["import", "-window", "root", out_path], out_path)

        return CaptureResult(
            ok=False,
            error="No screenshot tool found. Install one: gnome-screenshot, imagemagick (import), or grim (Wayland).",
        )

    def _run(self, cmd: list[str], out_path: str) -> CaptureResult:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)
            if proc.returncode != 0:
                return CaptureResult(ok=False, error=proc.stderr.strip() or f"{cmd[0]} failed")
            return CaptureResult(
                ok=True, path=out_path, active_window_title=self.active_window_title()
            )
        except subprocess.TimeoutExpired:
            return CaptureResult(ok=False, error=f"{cmd[0]} timed out")

    def active_window_title(self) -> str | None:
        if shutil.which("xdotool"):
            try:
                proc = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if proc.returncode == 0:
                    return proc.stdout.strip() or None
            except Exception:
                pass
        return None  # Wayland has no reliable cross-compositor way to get this

    def _wayland_outputs(self) -> list[str]:
        try:
            proc = subprocess.run(
                ["swaymsg", "-t", "get_outputs"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            import json

            return [o["name"] for o in json.loads(proc.stdout)]
        except Exception:
            return []

    def list_displays(self) -> list[dict]:
        names = self._wayland_outputs()
        if names:
            return [{"index": i, "name": n} for i, n in enumerate(names)]
        return [{"index": 0, "name": "primary"}]
