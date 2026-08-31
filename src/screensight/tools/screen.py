from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from screensight import core


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

    frame_path = Path(outcome.path)
    img_bytes = frame_path.read_bytes()
    img = Image(data=img_bytes, format="jpeg")
    result_parts.append(img)

    text_parts = [f"Active window: {outcome.active_window_title or 'unknown'}"]
    text_parts.append(f"Frame saved to: {outcome.path}")
    text_parts.append(f"SHA-256: {outcome.sha256}")
    if question:
        text_parts.append(f"Your question: {question}")
    result_parts.append("\n".join(text_parts))

    return result_parts


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


def register(mcp: FastMCP) -> None:
    mcp.tool(output_schema=None)(screen_capture)
    mcp.tool()(screen_list_displays)
