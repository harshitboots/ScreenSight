"""Bounded watch daemon — spawns a detached subprocess that polls
``core.capture_once()`` on an interval, writes status to daemon.json,
and self-terminates after *max_frames* changed frames or on error.

Public API (called by CLI and MCP server):
    start_daemon(interval, max_frames) -> dict
    stop_daemon() -> dict
    daemon_status() -> dict

The daemon loop lives at the bottom of this file and is invoked via
``python -m screensight.watch`` so it runs in its own OS process,
not as a thread inside the MCP server.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time

from .config import (
    DAEMON_PID_FILE,
    DAEMON_STATUS_FILE,
    DEFAULT_WATCH_INTERVAL,
    MAX_FRAMES_PER_WATCH,
    ensure_base_dir,
)
from .core import capture_once
from .diff import frame_changed
from .state import is_on, turn_off

# ── Public helpers ────────────────────────────────────────────────────

DEFAULT_INTERVAL = DEFAULT_WATCH_INTERVAL
DEFAULT_MAX_FRAMES = MAX_FRAMES_PER_WATCH


def start_daemon(interval: int = DEFAULT_INTERVAL, max_frames: int = DEFAULT_MAX_FRAMES) -> dict:
    """Spawn a detached ``screensight-watch`` subprocess and return its
    status dict.  If a daemon is already running, return that status
    instead of spawning a second one."""
    ensure_base_dir()

    existing = _read_pid()
    if existing and _process_alive(existing):
        return {"running": True, "pid": existing, "message": "daemon already running"}

    # Launch the daemon as a fully detached process.
    # On Windows creationflags=DETACHED_PROCESS + no stdio is the
    # equivalent of Unix setsid + devnull.
    cmd = [sys.executable, "-m", "screensight.watch", str(interval), str(max_frames)]
    kwargs: dict = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **kwargs)
    _write_pid(proc.pid)
    return {"running": True, "pid": proc.pid, "interval": interval, "max_frames": max_frames}


def stop_daemon() -> dict:
    """Send SIGTERM (or TerminateProcess on Windows) to the daemon, then
    clean up the pidfile and status file."""
    pid = _read_pid()
    if pid is None:
        _cleanup()
        return {"running": False, "message": "no daemon running"}

    if _process_alive(pid):
        try:
            if sys.platform == "win32":
                import ctypes

                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, False, pid)  # PROCESS_TERMINATE
                if handle:
                    kernel32.TerminateProcess(handle, 0)
                    kernel32.CloseHandle(handle)
            else:
                os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass  # already dead or we can't signal it — cleanup below is fine

    _cleanup()
    return {"running": False, "message": "daemon stopped", "pid": pid}


def daemon_status() -> dict:
    """Read ``daemon.json`` and return the daemon's last-known state."""
    ensure_base_dir()
    if DAEMON_STATUS_FILE.exists():
        try:
            data = json.loads(DAEMON_STATUS_FILE.read_text())
            # Verify the reported PID is still alive.
            pid = _read_pid()
            data["running"] = pid is not None and _process_alive(pid)
            return data
        except Exception:
            pass

    pid = _read_pid()
    return {"running": pid is not None and _process_alive(pid)}


# ── Internal pid helpers ──────────────────────────────────────────────


def _read_pid() -> int | None:
    ensure_base_dir()
    if not DAEMON_PID_FILE.exists():
        return None
    try:
        return int(DAEMON_PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def _write_pid(pid: int) -> None:
    ensure_base_dir()
    DAEMON_PID_FILE.write_text(str(pid))


def _process_alive(pid: int) -> bool:
    """Return True if *pid* is a running process we can signal."""
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # SYNCHRONIZE
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def _cleanup() -> None:
    """Remove the pidfile and status file."""
    DAEMON_PID_FILE.unlink(missing_ok=True)
    DAEMON_STATUS_FILE.unlink(missing_ok=True)


# ── Daemon loop (runs in the detached subprocess) ────────────────────


def _daemon_loop(interval: int, max_frames: int) -> None:
    """Core loop — called by ``__main__`` when this module is run directly.

    Every *interval* seconds it calls ``core.capture_once()``.  If the
    frame hasn't changed (same hash), it skips the status write.  After
    *max_frames* changed frames (or any error / SIGTERM) it writes a
    final status, turns the master switch off, and exits.
    """
    frame_count = 0
    last_hash: str | None = None

    def _write_status(**extra: object) -> None:
        ensure_base_dir()
        status: dict = {
            "frames_analyzed": frame_count,
            "last_hash": last_hash,
            "interval": interval,
            "max_frames": max_frames,
            "timestamp": time.time(),
        }
        status.update(extra)
        DAEMON_STATUS_FILE.write_text(json.dumps(status, indent=2))

    def _shutdown(signum: int | None = None, _frame: object = None) -> None:
        _write_status(status="stopped")
        turn_off()
        _cleanup()
        sys.exit(0)

    # Register signal handlers for graceful shutdown.
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    _write_status(status="running")

    while frame_count < max_frames:
        if not is_on():
            _write_status(status="stopped", reason="switch_off")
            _cleanup()
            return

        time.sleep(interval)

        outcome = capture_once()
        if not outcome.ok:
            # Error or blocked — stop the daemon.
            _write_status(status="error", error=outcome.error)
            turn_off()
            _cleanup()
            return

        if outcome.sha256 and frame_changed(outcome.sha256, last_hash):
            last_hash = outcome.sha256
            frame_count += 1
            _write_status(status="running")

    # Reached max_frames — stop gracefully.
    _write_status(status="stopped", reason="max_frames")
    turn_off()
    _cleanup()


# ── Entry point for ``python -m screensight.watch`` ──────────────────

if __name__ == "__main__":
    if len(sys.argv) == 3:
        _interval = int(sys.argv[1])
        _max = int(sys.argv[2])
    else:
        _interval = DEFAULT_INTERVAL
        _max = DEFAULT_MAX_FRAMES
    _daemon_loop(_interval, _max)
