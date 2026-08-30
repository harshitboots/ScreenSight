"""Two independent layers of protection, on top of the master on/off switch:

1. Title blocklist — if the frontmost app/window title matches something in
   the blocklist (password managers, private-browsing windows, etc.), the
   capture is refused before the image is even written to disk.
2. Zone redaction — user-defined screen rectangles (e.g. where a banking
   app always opens) get blacked out in the saved frame.

Neither layer is a substitute for the master switch — turn screensight off
before doing anything sensitive. This just catches the "forgot to turn it
off" case.
"""

from __future__ import annotations

from PIL import Image

from .config import MAX_LONG_EDGE, load_redact_config


def title_is_blocked(title: str | None) -> bool:
    if not title:
        return False
    cfg = load_redact_config()
    lowered = title.lower()
    return any(term.lower() in lowered for term in cfg.get("blocklist", []))


def process_frame(path: str) -> None:
    """Downscale to keep tokens low, and black out any configured redact zones.
    Mutates the file in place."""
    cfg = load_redact_config()
    zones = cfg.get("zones", [])

    with Image.open(path) as img:
        img = img.convert("RGB")

        # downscale — 1568px long edge is past the point more pixels help a vision model
        w, h = img.size
        long_edge = max(w, h)
        if long_edge > MAX_LONG_EDGE:
            scale = MAX_LONG_EDGE / long_edge
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            zones = [_scale_zone(z, scale) for z in zones]

        if zones:
            from PIL import ImageDraw

            draw = ImageDraw.Draw(img)
            for z in zones:
                draw.rectangle([z["x"], z["y"], z["x"] + z["w"], z["y"] + z["h"]], fill="black")

        img.save(path, "JPEG", quality=85)


def _scale_zone(zone: dict, scale: float) -> dict:
    return {k: (v * scale if k != "label" else v) for k, v in zone.items()}
