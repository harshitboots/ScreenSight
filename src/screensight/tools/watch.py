from __future__ import annotations

from fastmcp import FastMCP

from screensight import watch as _watch


def screen_watch_start(
    interval: int = 5,
    max_frames: int = 10,
) -> str:
    """Start a bounded watch session that captures the screen on an interval.

    Spawns a background daemon that takes a screenshot every `interval`
    seconds, skipping unchanged frames. Stops automatically after
    `max_frames` changed frames to avoid burning tokens.

    The daemon writes its status to ~/.screensight/daemon.json so you
    can poll progress with screen_watch_latest.

    Args:
        interval: Seconds between capture attempts (default 5).
        max_frames: Maximum changed frames before auto-stop (default 10).
    """
    result = _watch.start_daemon(interval=interval, max_frames=max_frames)
    return f"Watch daemon started: {result}"


def screen_watch_stop() -> str:
    """Stop a running watch daemon.

    Sends SIGTERM to the background daemon process and cleans up
    the pidfile and status file. Safe to call even if no daemon is running.
    """
    result = _watch.stop_daemon()
    return f"Watch daemon stopped: {result}"


def screen_watch_latest() -> str:
    """Get the latest status from the watch daemon.

    Returns how many frames have been analyzed, the last frame hash,
    whether the daemon is still running, and the interval/max config.
    Useful for checking progress of a running watch session.
    """
    status = _watch.daemon_status()
    running = status.get("running", False)
    frames = status.get("frames_analyzed", 0)
    last_hash = status.get("last_hash", "none")
    reason = status.get("reason", "")
    daemon_status = status.get("status", "unknown")

    lines = [
        f"Daemon running: {running}",
        f"Status: {daemon_status}",
        f"Frames analyzed: {frames}",
        f"Last hash: {last_hash}",
    ]
    if reason:
        lines.append(f"Stop reason: {reason}")
    if status.get("interval"):
        lines.append(f"Interval: {status['interval']}s")
    if status.get("max_frames"):
        lines.append(f"Max frames: {status['max_frames']}")

    return "\n".join(lines)


def register(mcp: FastMCP) -> None:
    mcp.tool()(screen_watch_start)
    mcp.tool()(screen_watch_stop)
    mcp.tool()(screen_watch_latest)
