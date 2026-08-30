from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from ..config import WSL_PATH_CONVERT_TIMEOUT, WSL_TEMP_DIR_TIMEOUT
from .base import CaptureBackend, CaptureResult


def is_wsl2() -> bool:
    """Detect if running inside WSL2 (vs WSL1 or native Linux).
    
    WSL2 uses a real Linux kernel with a lightweight VM, while WSL1
    is a syscall translation layer. Path translation works differently
    between them.
    """
    try:
        proc = subprocess.run(
            ["wsl.exe", "--list", "--verbose"],
            capture_output=True, text=True, timeout=5,
        )
        # WSL2 output contains version info; look for version 2
        # Output format: "  Ubuntu    Running    2"
        return "2" in proc.stdout
    except Exception:
        return True  # assume WSL2 if we can't determine


def win_to_wsl_path(win_path: str) -> str:
    """Convert a Windows path (C:\\Users\\...) to WSL path (/mnt/c/Users/...).
    
    Requires wslpath utility (included in WSL2 distributions).
    """
    if not shutil.which("wslpath"):
        raise RuntimeError("wslpath not found — required for WSL path translation")
    
    proc = subprocess.run(
        ["wslpath", "-u", win_path],
        capture_output=True, text=True, timeout=WSL_PATH_CONVERT_TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"wslpath failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def wsl_to_win_path(wsl_path: str) -> str:
    """Convert a WSL path (/mnt/c/...) to Windows path (C:\\Users\\...).
    
    Requires wslpath utility (included in WSL2 distributions).
    """
    if not shutil.which("wslpath"):
        raise RuntimeError("wslpath not found — required for WSL path translation")
    
    proc = subprocess.run(
        ["wslpath", "-w", wsl_path],
        capture_output=True, text=True, timeout=WSL_PATH_CONVERT_TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"wslpath failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def get_windows_temp_dir() -> str:
    """Get the Windows TEMP directory from inside WSL.
    
    Uses powershell.exe to read $env:TEMP, which returns the Windows path.
    """
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", "$env:TEMP"],
        capture_output=True, text=True, timeout=WSL_TEMP_DIR_TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to get Windows TEMP dir: {proc.stderr.strip()}")
    return proc.stdout.strip()

_PS_SCRIPT = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save('{out_path}', [System.Drawing.Imaging.ImageFormat]::Jpeg)
$graphics.Dispose(); $bmp.Dispose()

Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class ActiveWin {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
}
'@
$h = [ActiveWin]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[void][ActiveWin]::GetWindowText($h, $sb, 256)
Write-Output $sb.ToString()
"""

_PS_TITLE_SCRIPT = r"""
Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class ActiveWin {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
}
'@
$h = [ActiveWin]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[void][ActiveWin]::GetWindowText($h, $sb, 256)
Write-Output $sb.ToString()
"""


class WindowsCapture(CaptureBackend):
    def screenshot(self, out_path: str, display: Optional[int] = None) -> CaptureResult:
        script = _PS_SCRIPT.replace("{out_path}", out_path.replace("\\", "\\\\"))
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=20,
            )
            if proc.returncode != 0:
                return CaptureResult(ok=False, error=proc.stderr.strip() or "PowerShell capture failed")
            title = proc.stdout.strip() or None
            return CaptureResult(ok=True, path=out_path, active_window_title=title)
        except FileNotFoundError:
            return CaptureResult(ok=False, error="powershell.exe not found")
        except subprocess.TimeoutExpired:
            return CaptureResult(ok=False, error="PowerShell capture timed out")

    def active_window_title(self) -> Optional[str]:
        """Get the active window title via PowerShell DllImport.
        
        Returns None if PowerShell invocation fails — callers must treat
        None as 'unknown', not 'safe'.
        """
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", _PS_TITLE_SCRIPT],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception:
            pass
        return None

    def list_displays(self) -> list[dict]:
        """List displays available on Windows via PowerShell."""
        script = """
        Add-Type -AssemblyName System.Windows.Forms
        $screens = [System.Windows.Forms.Screen]::AllScreens
        for ($i = 0; $i -lt $screens.Count; $i++) {
            $s = $screens[$i]
            Write-Output "$i|$($s.DeviceName)|$($s.Bounds.Width)x$($s.Bounds.Height)"
        }
        """
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                displays = []
                for line in proc.stdout.strip().splitlines():
                    parts = line.split("|")
                    if len(parts) == 3:
                        displays.append({
                            "index": int(parts[0]),
                            "name": parts[1].strip("\\"),
                            "resolution": parts[2],
                        })
                return displays or [{"index": 0, "name": "primary"}]
        except Exception:
            pass
        return [{"index": 0, "name": "primary"}]


class WSLCapture(WindowsCapture):
    """From inside WSL, capture the real Windows desktop, then copy the
    result back across the filesystem boundary into WSL's temp dir.
    
    Requirements:
    - WSL2 (not WSL1) with wslpath utility
    - powershell.exe accessible from WSL PATH
    - Write access to Windows TEMP directory
    """

    def screenshot(self, out_path: str, display: Optional[int] = None) -> CaptureResult:
        # Check for required tools
        if not shutil.which("powershell.exe"):
            return CaptureResult(
                ok=False,
                error="powershell.exe not found — required for WSL capture"
            )
        
        try:
            win_tmp = get_windows_temp_dir()
        except RuntimeError as e:
            return CaptureResult(ok=False, error=str(e))
        
        win_out = f"{win_tmp}\\screensight-frame.jpg"
        
        # Capture using Windows backend (writes to Windows filesystem)
        result = super().screenshot(win_out, display)
        if not result.ok:
            return result
        
        # Convert Windows path to WSL path and copy across filesystem boundary
        try:
            wsl_path = win_to_wsl_path(win_out)
        except RuntimeError as e:
            return CaptureResult(ok=False, error=f"Path translation failed: {e}")
        
        try:
            wsl_path_obj = Path(wsl_path)
            if not wsl_path_obj.exists():
                return CaptureResult(
                    ok=False,
                    error=f"Captured file not found at WSL path: {wsl_path}"
                )
            
            # Copy bytes across filesystem boundary
            Path(out_path).write_bytes(wsl_path_obj.read_bytes())
            
            # Clean up Windows temp file
            wsl_path_obj.unlink(missing_ok=True)
            
            return CaptureResult(
                ok=True,
                path=out_path,
                active_window_title=result.active_window_title,
            )
        except Exception as e:
            return CaptureResult(ok=False, error=f"WSL copy-back failed: {e}")

    def active_window_title(self) -> Optional[str]:
        """Get the active window title from Windows host.
        
        Tries PowerShell DllImport first (works in most WSL2 setups).
        Falls back to None if PowerShell invocation fails.
        """
        try:
            return super().active_window_title()
        except Exception:
            return None  # Unknown — callers treat None as "not verified safe"

    def list_displays(self) -> list[dict]:
        """List displays available on the Windows host from WSL."""
        return super().list_displays()
