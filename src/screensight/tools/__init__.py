from __future__ import annotations

from fastmcp import FastMCP

from . import audio, control, screen
from . import watch as watch_tools


def register_all(mcp: FastMCP) -> None:
    """Register every ScreenSight tool onto *mcp* in domain order."""
    control.register(mcp)
    screen.register(mcp)
    audio.register(mcp)
    watch_tools.register(mcp)
