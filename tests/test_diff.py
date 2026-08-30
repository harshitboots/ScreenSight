"""Tests for hash stability and change detection (diff.py)."""

from __future__ import annotations

from screensight.diff import frame_changed, sha256_of_file


def test_sha256_stability(tmp_path):
    """Same file content always produces the same hash."""
    f = tmp_path / "test.bin"
    f.write_bytes(b"hello world")
    h1 = sha256_of_file(str(f))
    h2 = sha256_of_file(str(f))
    assert h1 == h2


def test_sha256_different_content():
    """Different content produces different hashes."""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False) as a:
        a.write(b"content A")
        path_a = a.name
    with tempfile.NamedTemporaryFile(delete=False) as b:
        b.write(b"content B")
        path_b = b.name

    try:
        assert sha256_of_file(path_a) != sha256_of_file(path_b)
    finally:
        os.unlink(path_a)
        os.unlink(path_b)


def test_frame_changed_first_frame():
    """First frame (no previous hash) is always 'changed'."""
    assert frame_changed("abc123", None) is True


def test_frame_changed_same_hash():
    """Same hash means no change."""
    assert frame_changed("abc123", "abc123") is False


def test_frame_changed_different_hash():
    """Different hash means change detected."""
    assert frame_changed("abc123", "def456") is True
