"""Tests for the master on/off switch (state.py)."""

from __future__ import annotations

from screensight import state


def test_initial_state_is_off(tmp_path, monkeypatch):
    """State file doesn't exist yet → is_on() returns False."""
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    assert state.is_on() is False


def test_turn_on_then_is_on(tmp_path, monkeypatch):
    """turn_on() makes is_on() return True."""
    sf = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_FILE", sf)
    state.turn_on()
    assert state.is_on() is True


def test_round_trip_on_off(tmp_path, monkeypatch):
    """on → off → on works correctly."""
    sf = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_FILE", sf)

    state.turn_on()
    assert state.is_on() is True

    state.turn_off()
    assert state.is_on() is False

    state.turn_on()
    assert state.is_on() is True


def test_status_dict(tmp_path, monkeypatch):
    """status() returns expected keys."""
    sf = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_FILE", sf)

    state.turn_on()
    s = state.status()
    assert s["enabled"] is True
    assert s["since"] is not None


def test_corrupt_state_file(tmp_path, monkeypatch):
    """A corrupt state file is treated as 'off'."""
    sf = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_FILE", sf)
    sf.write_text("not valid json {{{")
    assert state.is_on() is False
