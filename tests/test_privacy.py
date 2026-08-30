"""Tests for blocklist matching and redact-zone coordinate scaling."""

from __future__ import annotations

from screensight.privacy import _scale_zone, process_frame, title_is_blocked

# ── Blocklist matching ────────────────────────────────────────────────


def test_blocklist_case_insensitive():
    """Matching is case-insensitive."""
    assert title_is_blocked("1Password") is True
    assert title_is_blocked("1password") is True
    assert title_is_blocked("1PASSWORD") is True


def test_blocklist_substring():
    """Partial matches trigger the blocklist."""
    assert title_is_blocked("My 1Password Vault") is True
    assert title_is_blocked("Bitwarden - Firefox") is True


def test_blocklist_no_match():
    """Non-sensitive titles pass through."""
    assert title_is_blocked("Visual Studio Code") is False
    assert title_is_blocked("Terminal") is False
    assert title_is_blocked("Google Chrome") is False


def test_blocklist_none_title():
    """None title is treated as 'unknown', not blocked."""
    assert title_is_blocked(None) is False


def test_blocklist_empty_title():
    """Empty string is not blocked."""
    assert title_is_blocked("") is False


# ── Zone scaling ──────────────────────────────────────────────────────


def test_scale_zone_scales_coordinates():
    """_scale_zone multiplies numeric fields by the scale factor."""
    zone = {"x": 100, "y": 200, "w": 300, "h": 400, "label": "banking"}
    scaled = _scale_zone(zone, 0.5)
    assert scaled == {"x": 50, "y": 100, "w": 150, "h": 200, "label": "banking"}


def test_scale_zone_preserves_label():
    """The 'label' field is not scaled."""
    zone = {"x": 10, "y": 20, "w": 30, "h": 40, "label": "test"}
    scaled = _scale_zone(zone, 2.0)
    assert scaled["label"] == "test"


def test_scale_zone_identity():
    """Scale of 1.0 leaves coordinates unchanged."""
    zone = {"x": 50, "y": 60, "w": 70, "h": 80}
    scaled = _scale_zone(zone, 1.0)
    assert scaled == zone


# ── process_frame integration ─────────────────────────────────────────


def test_process_frame_downscales(tmp_path, monkeypatch):
    """process_frame downscales images longer than MAX_LONG_EDGE."""
    from PIL import Image

    from screensight import privacy

    img_path = tmp_path / "test.jpg"
    # Create a 3000x1000 image (long edge = 3000)
    img = Image.new("RGB", (3000, 1000), color="red")
    img.save(str(img_path), "JPEG")

    monkeypatch.setattr(privacy, "MAX_LONG_EDGE", 1568)
    process_frame(str(img_path))

    with Image.open(str(img_path)) as result:
        w, h = result.size
        # Allow ±1 for integer rounding during resize
        assert abs(max(w, h) - 1568) <= 1


def test_process_frame_applies_zones(tmp_path, monkeypatch):
    """process_frame blacks out configured redact zones."""
    from PIL import Image

    from screensight import privacy

    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (1000, 1000), color="white")
    img.save(str(img_path), "JPEG")

    # Configure a zone and no downscaling
    config = {"blocklist": [], "zones": [{"x": 0, "y": 0, "w": 100, "h": 100}]}
    monkeypatch.setattr(privacy, "load_redact_config", lambda: config)
    monkeypatch.setattr(privacy, "MAX_LONG_EDGE", 10000)  # no downscale

    process_frame(str(img_path))

    with Image.open(str(img_path)) as result:
        # Check the pixel at (50, 50) is black (inside the zone)
        pixel = result.getpixel((50, 50))
        assert pixel == (0, 0, 0)
        # Check a pixel outside the zone is still white
        pixel_outside = result.getpixel((500, 500))
        assert pixel_outside == (255, 255, 255)
