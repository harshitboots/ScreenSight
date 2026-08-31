"""FastMCP server exposing ScreenSight as 9 tools for any MCP-capable agent.

Every tool docstring is written for the *calling agent* (AGENTS.md rule 8)
— treat them as man-page entries, not code comments.

Tools are organised by domain under screensight/tools/:
  control.py  — screen_enable, screen_disable, screen_status
  screen.py   — screen_capture, screen_list_displays
  audio.py    — screen_capture_audio
  watch.py    — screen_watch_start, screen_watch_stop, screen_watch_latest
"""

from __future__ import annotations

from fastmcp import FastMCP

from .tools import register_all

mcp = FastMCP(
    "screensight",
    instructions=(
        "ScreenSight lets you see the user's screen. "
        "Use screen_capture to take a screenshot, then examine the image "
        "to understand what's on screen. The master switch must be on "
        "(screen_enable) before any capture works."
    ),
)

register_all(mcp)


def run() -> None:
    """Entry point for the `screensight-mcp` console script."""
    mcp.run()


if __name__ == "__main__":
    run()
