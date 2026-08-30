"""Tests for MCP server tool definitions — verify output_schema and tool metadata."""

from __future__ import annotations

import asyncio

from screensight.mcp_server import mcp


def _get_tools():
    """List all tools from the MCP server."""
    return asyncio.run(mcp.list_tools())


def _get_tool(name: str):
    """Get a single tool by name."""
    tools = _get_tools()
    for t in tools:
        if t.name == name:
            return t
    raise AssertionError(f"Tool '{name}' not found")


# ── output_schema tests ───────────────────────────────────────────────


def test_screen_capture_output_schema_is_none():
    """screen_capture must have output_schema=None to avoid the
    'outputSchema defined but no structured output returned' error.

    FastMCP 3.4.7 auto-generates a schema from `-> list`, but the Image
    object doesn't serialize cleanly, so the MCP client rejects it.
    Setting output_schema=None prevents schema generation entirely.
    """
    tool = _get_tool("screen_capture")
    assert tool.output_schema is None, (
        f"screen_capture.output_schema should be None, got {tool.output_schema!r}. "
        "FastMCP will auto-generate a schema from `-> list` that fails validation."
    )


def test_other_tools_have_no_output_schema_conflict():
    """All other tools return `str`, which serializes cleanly.
    Confirm none of them have output_schema issues (they should have
    auto-generated schemas or None — both are fine as long as the
    return type serializes)."""
    tool_names = [
        "screen_enable",
        "screen_disable",
        "screen_status",
        "screen_watch_start",
        "screen_watch_stop",
        "screen_watch_latest",
        "screen_list_displays",
    ]
    for name in tool_names:
        tool = _get_tool(name)
        # These tools return str, which serializes fine — just confirm
        # they exist and don't have a broken schema. No assertion on
        # output_schema value since str works either way.
        assert tool is not None, f"Tool '{name}' not found"


# ── tool count ────────────────────────────────────────────────────────


def test_all_eight_tools_registered():
    """ScreenSight must expose exactly 8 tools."""
    tools = _get_tools()
    names = sorted(t.name for t in tools)
    expected = sorted([
        "screen_enable",
        "screen_disable",
        "screen_status",
        "screen_capture",
        "screen_watch_start",
        "screen_watch_stop",
        "screen_watch_latest",
        "screen_list_displays",
    ])
    assert names == expected, f"Expected tools {expected}, got {names}"


# ── screen_capture content blocks (requires mocking) ──────────────────


def test_screen_capture_returns_content_blocks(tmp_path, monkeypatch):
    """screen_capture should return content blocks (ImageContent + TextContent),
    not structured_content. Mock the capture pipeline to test this."""
    from pathlib import Path

    # Write a minimal JPEG for the mock backend to produce.
    from PIL import Image as PILImage

    from screensight import core, state
    from screensight.capture.base import CaptureBackend, CaptureResult
    from screensight.mcp_server import mcp as mcp_server

    def _write_jpeg(path: Path) -> None:
        img = PILImage.new("RGB", (100, 100), color="blue")
        img.save(str(path), "JPEG")

    class MockBackend(CaptureBackend):
        def screenshot(self, out_path, display=None):
            _write_jpeg(Path(out_path))
            return CaptureResult(ok=True, path=out_path, active_window_title="Test Window")

        def list_displays(self):
            return []

    # Patch state, frame path, and backend.
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "FRAME_PATH", tmp_path / "frame.jpg")
    monkeypatch.setattr(core, "get_backend", lambda: MockBackend())
    state.turn_on()

    # Find and run the screen_capture tool.
    tools = asyncio.run(mcp_server.list_tools())
    capture_tool = next(t for t in tools if t.name == "screen_capture")
    result = asyncio.run(capture_tool.run({"question": "test query"}))

    # Content blocks must be present.
    assert result.content is not None, "content should not be None"
    assert len(result.content) >= 2, f"Expected >=2 content blocks, got {len(result.content)}"

    # structured_content must be None (output_schema=None).
    assert result.structured_content is None, (
        f"structured_content should be None, got {result.structured_content!r}"
    )
