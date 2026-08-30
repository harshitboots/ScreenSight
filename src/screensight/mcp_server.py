"""FastMCP server exposing ScreenSight as 8 tools for any MCP-capable agent.

Every tool docstring is written for the *calling agent* (AGENTS.md rule 8)
— treat them as man-page entries, not code comments.
"""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from . import core, state, watch

mcp = FastMCP(
    "screensight",
    instructions=(
        "ScreenSight lets you see the user's screen. "
        "Use screen_capture to take a screenshot, then examine the image "
        "to understand what's on screen. The master switch must be on "
        "(screen_enable) before any capture works."
    ),
)


# ── 1. screen_enable ──────────────────────────────────────────────────


@mcp.tool()
def screen_enable() -> str:
    """Turn ON the ScreenSight master switch.

    The master switch must be ON before any screen capture can happen.
    This is a safety gate — nothing is captured while it's off.
    Call this before screen_capture if you're unsure whether it's on.

    Returns the current state as JSON.
    """
    state.turn_on()
    s = state.status()
    return f"ScreenSight enabled. State: {s}"


# ── 2. screen_disable ─────────────────────────────────────────────────


@mcp.tool()
def screen_disable() -> str:
    """Turn OFF the ScreenSight master switch.

    Disables all screen capture. Any running watch daemon will
    also stop. The frame file (if any) is NOT deleted by this call —
    use this when you want to temporarily pause captures.

    Returns the current state as JSON.
    """
    state.turn_off()
    s = state.status()
    return f"ScreenSight disabled. State: {s}"


# ── 3. screen_status ──────────────────────────────────────────────────


@mcp.tool()
def screen_status() -> str:
    """Check whether ScreenSight's master switch is on or off.

    Returns enabled/disabled status and when it was last changed.
    Call this to verify the switch state before attempting a capture.
    """
    s = state.status()
    enabled = "ON" if s["enabled"] else "OFF"
    return f"ScreenSight is {enabled}. Details: {s}"


# ── 4. screen_capture ─────────────────────────────────────────────────


@mcp.tool(output_schema=None)
def screen_capture(
    question: str = "",
    display: int | None = None,
) -> list:
    """Capture the user's screen and return the image for you to examine.

    Takes a screenshot of the specified display (or the primary display
    if none is specified). Returns the captured image as a visual content
    block along with the active window title as text.

    If you provide a `question`, it will be echoed back so you can
    address it while examining the image — the tool does not call
    another model; *you* do the looking.

    The master switch must be ON (screen_enable) before this works.
    If the active window matches the blocklist (password managers,
    private-browsing windows), the capture is refused for safety.

    Args:
        question: Optional question to echo back for your context.
        display: Display index (omit for primary display).

    Returns:
        Image content block + window title text (+ echoed question if given).
    """
    outcome = core.capture_once(display=display)
    if not outcome.ok:
        return [f"Capture failed: {outcome.error}"]

    result_parts: list = []

    # Read the frame file and return as an MCP Image.
    frame_path = Path(outcome.path)
    img_bytes = frame_path.read_bytes()
    img = Image(data=img_bytes, format="jpeg")
    result_parts.append(img)

    # Text context for the agent.
    text_parts = [f"Active window: {outcome.active_window_title or 'unknown'}"]
    text_parts.append(f"Frame saved to: {outcome.path}")
    text_parts.append(f"SHA-256: {outcome.sha256}")
    if question:
        text_parts.append(f"Your question: {question}")
    result_parts.append("\n".join(text_parts))

    return result_parts


# ── 5. screen_watch_start ─────────────────────────────────────────────


@mcp.tool()
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
    result = watch.start_daemon(interval=interval, max_frames=max_frames)
    return f"Watch daemon started: {result}"


# ── 6. screen_watch_stop ──────────────────────────────────────────────


@mcp.tool()
def screen_watch_stop() -> str:
    """Stop a running watch daemon.

    Sends SIGTERM to the background daemon process and cleans up
    the pidfile and status file. Safe to call even if no daemon is running.
    """
    result = watch.stop_daemon()
    return f"Watch daemon stopped: {result}"


# ── 7. screen_watch_latest ────────────────────────────────────────────


@mcp.tool()
def screen_watch_latest() -> str:
    """Get the latest status from the watch daemon.

    Returns how many frames have been analyzed, the last frame hash,
    whether the daemon is still running, and the interval/max config.
    Useful for checking progress of a running watch session.
    """
    status = watch.daemon_status()
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


# ── 8. screen_list_displays ───────────────────────────────────────────


@mcp.tool()
def screen_list_displays() -> str:
    """List all available displays/monitors.

    Returns display index, name, and dimensions for each connected
    monitor. Use the display index with screen_capture to capture
    a specific monitor.
    """
    displays = core.list_displays()
    if not displays:
        return "No displays found."

    lines = ["Available displays:"]
    for d in displays:
        lines.append(
            f"  Display {d.get('index', '?')}: "
            f"{d.get('name', 'unknown')} "
            f"({d.get('width', '?')}x{d.get('height', '?')})"
        )
    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────


def run() -> None:
    """Entry point for the `screensight-mcp` console script."""
    mcp.run()


if __name__ == "__main__":
    run()
