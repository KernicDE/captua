"""Tests for JSON settings persistence."""
import json
from pathlib import Path

import pytest

from captua.settings import _default_settings, load_settings, save_settings


@pytest.fixture()
def settings_dir(tmp_path, monkeypatch):
    """Redirect CONFIG_DIR and CONFIG_FILE to a temp directory."""
    import captua.settings as mod

    monkeypatch.setattr(mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(mod, "CONFIG_FILE", tmp_path / "settings.json")
    return tmp_path


def test_load_returns_defaults_when_no_file(settings_dir):
    result = load_settings()
    assert result == _default_settings()


def test_save_and_load_round_trip(settings_dir):
    data = _default_settings()
    data["backdrop_padding"] = 99
    save_settings(data)
    loaded = load_settings()
    assert loaded["backdrop_padding"] == 99


def test_load_merges_missing_keys(settings_dir):
    """Saved file missing new keys should still get defaults for those keys."""
    partial = {"backdrop_padding": 50}
    (settings_dir / "settings.json").write_text(json.dumps(partial))
    loaded = load_settings()
    assert loaded["backdrop_padding"] == 50
    assert "line_color" in loaded  # default key filled in


def test_load_recovers_from_corrupt_file(settings_dir):
    (settings_dir / "settings.json").write_text("not valid json{{")
    result = load_settings()
    assert result == _default_settings()


def test_save_is_atomic(settings_dir):
    """save_settings must not leave a .settings.tmp file behind."""
    data = _default_settings()
    save_settings(data)
    assert not (settings_dir / ".settings.tmp").exists()
    assert (settings_dir / "settings.json").exists()


def test_save_creates_directory(tmp_path, monkeypatch):
    nested = tmp_path / "a" / "b" / "captua"
    import captua.settings as mod

    monkeypatch.setattr(mod, "CONFIG_DIR", nested)
    monkeypatch.setattr(mod, "CONFIG_FILE", nested / "settings.json")
    save_settings(_default_settings())
    assert (nested / "settings.json").exists()
