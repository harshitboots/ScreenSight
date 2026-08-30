"""ScreenSight CLI — for any coding agent that can shell out to a command,
even if it has no MCP support (e.g. Aider, custom scripts, shell-based agents).

Usage:
    screensight on
    screensight off
    screensight status
    screensight capture [--display N]
    screensight watch [--interval N] [--max-frames N]
    screensight watch-stop
    screensight watch-status
    screensight displays
"""

from __future__ import annotations

import argparse
import json
import sys

from . import core, state, watch


def cmd_on(args: argparse.Namespace) -> None:
    state.turn_on()
    print(json.dumps(state.status()))


def cmd_off(args: argparse.Namespace) -> None:
    state.turn_off()
    print(json.dumps(state.status()))


def cmd_status(args: argparse.Namespace) -> None:
    print(json.dumps(state.status()))


def cmd_capture(args: argparse.Namespace) -> None:
    outcome = core.capture_once(display=args.display)
    if not outcome.ok:
        print(json.dumps({"error": outcome.error}), file=sys.stderr)
        sys.exit(3)
    print(
        json.dumps(
            {
                "path": outcome.path,
                "sha256": outcome.sha256,
                "active_window_title": outcome.active_window_title,
            }
        )
    )


def cmd_watch(args: argparse.Namespace) -> None:
    result = watch.start_daemon(
        interval=args.interval,
        max_frames=args.max_frames,
    )
    print(json.dumps(result))


def cmd_watch_stop(args: argparse.Namespace) -> None:
    result = watch.stop_daemon()
    print(json.dumps(result))


def cmd_watch_status(args: argparse.Namespace) -> None:
    result = watch.daemon_status()
    print(json.dumps(result))


def cmd_displays(args: argparse.Namespace) -> None:
    displays = core.list_displays()
    print(json.dumps(displays))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="screensight",
        description="Universal screen-awareness for coding agents.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("on", help="Enable screen capture access")
    sub.add_parser("off", help="Disable screen capture access")
    sub.add_parser("status", help="Check whether screen access is on")

    cap = sub.add_parser("capture", help="Capture the current screen")
    cap.add_argument("--display", type=int, default=None, help="Display index (omit for primary)")

    w = sub.add_parser("watch", help="Start a bounded watch session")
    w.add_argument(
        "--interval",
        type=int,
        default=watch.DEFAULT_INTERVAL,
        help="Seconds between polls (default: %(default)s)",
    )
    w.add_argument(
        "--max-frames",
        type=int,
        default=watch.DEFAULT_MAX_FRAMES,
        help="Max changed frames before auto-stop (default: %(default)s)",
    )

    sub.add_parser("watch-stop", help="Stop a running watch daemon")
    sub.add_parser("watch-status", help="Check watch daemon status")
    sub.add_parser("displays", help="List available displays")

    args = parser.parse_args()

    commands = {
        "on": cmd_on,
        "off": cmd_off,
        "status": cmd_status,
        "capture": cmd_capture,
        "watch": cmd_watch,
        "watch-stop": cmd_watch_stop,
        "watch-status": cmd_watch_status,
        "displays": cmd_displays,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
