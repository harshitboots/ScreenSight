from __future__ import annotations

from fastmcp import FastMCP

from screensight import state


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


def screen_status() -> str:
    """Check whether ScreenSight's master switch is on or off.

    Returns enabled/disabled status and when it was last changed.
    Call this to verify the switch state before attempting a capture.
    """
    s = state.status()
    enabled = "ON" if s["enabled"] else "OFF"
    return f"ScreenSight is {enabled}. Details: {s}"


def register(mcp: FastMCP) -> None:
    mcp.tool()(screen_enable)
    mcp.tool()(screen_disable)
    mcp.tool()(screen_status)
