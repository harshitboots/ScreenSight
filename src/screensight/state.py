"""The master switch. Off by default. Nothing in this package captures a
pixel unless this file says 'on' — checked at the point of capture itself,
not just in whichever prompt/tool description an agent happens to read.
"""

from __future__ import annotations

import json
import time

from .config import FRAME_PATH, STATE_FILE, ensure_base_dir


def is_on() -> bool:
    ensure_base_dir()
    if not STATE_FILE.exists():
        return False
    try:
        data = json.loads(STATE_FILE.read_text())
        return bool(data.get("enabled", False))
    except Exception:
        return False


def turn_on() -> None:
    ensure_base_dir()
    STATE_FILE.write_text(json.dumps({"enabled": True, "since": time.time()}))


def turn_off() -> None:
    ensure_base_dir()
    STATE_FILE.write_text(json.dumps({"enabled": False, "since": time.time()}))
    # Frame hygiene: delete the frame file on off.
    FRAME_PATH.unlink(missing_ok=True)


def status() -> dict:
    ensure_base_dir()
    on = is_on()
    since = None
    if STATE_FILE.exists():
        try:
            since = json.loads(STATE_FILE.read_text()).get("since")
        except Exception:
            pass
    return {"enabled": on, "since": since}
