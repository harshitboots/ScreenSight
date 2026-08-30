"""Central config: all paths under ~/.screensight, nothing scattered."""

from __future__ import annotations

import json
import platform
from pathlib import Path

HOME = Path.home()
BASE_DIR = HOME / ".screensight"
FRAME_PATH = BASE_DIR / "frame.jpg"
STATE_FILE = BASE_DIR / "state.json"  # master on/off switch
DAEMON_STATUS_FILE = BASE_DIR / "daemon.json"  # written by the watch daemon
DAEMON_PID_FILE = BASE_DIR / "daemon.pid"
REDACT_ZONES_FILE = BASE_DIR / "redact_zones.json"
LOG_FILE = BASE_DIR / "screensight.log"

MAX_LONG_EDGE = 1568  # matches Claude's vision sweet spot, keeps tokens low
DEFAULT_WATCH_INTERVAL = 5  # seconds
MAX_FRAMES_PER_WATCH = 10  # hard cap so a forgotten daemon can't burn context/tokens
AUTO_OFF_ON_WATCH_END = True

# WSL-specific timeouts (PowerShell via WSL is slower than native Windows)
WSL_CAPTURE_TIMEOUT = 30       # seconds — PowerShell capture from WSL
WSL_PATH_CONVERT_TIMEOUT = 5   # seconds — wslpath conversion
WSL_TEMP_DIR_TIMEOUT = 10      # seconds — getting $env:TEMP from PowerShell

# Window/app titles that cause capture to be skipped outright (case-insensitive substrings).
# User can extend this in ~/.screensight/redact_zones.json -> "blocklist": [...]
DEFAULT_TITLE_BLOCKLIST = [
    "1password",
    "bitwarden",
    "keychain access",
    "keepass",
    "lastpass",
    "password",
    "private browsing",
    "incognito",
]


def ensure_base_dir() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def get_os() -> str:
    system = platform.system().lower()
    if system == "linux" and "microsoft" in platform.uname().release.lower():
        return "wsl"
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def load_redact_config() -> dict:
    ensure_base_dir()
    if not REDACT_ZONES_FILE.exists():
        default = {"blocklist": DEFAULT_TITLE_BLOCKLIST, "zones": []}
        REDACT_ZONES_FILE.write_text(json.dumps(default, indent=2))
        return default
    try:
        return json.loads(REDACT_ZONES_FILE.read_text())
    except Exception:
        return {"blocklist": DEFAULT_TITLE_BLOCKLIST, "zones": []}
