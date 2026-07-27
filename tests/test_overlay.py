"""Tests for the overlay window: copy pipeline, Esc hierarchy, sticky tools,
settings persistence."""

import json
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QImage, QKeyEvent, QPixmap

import captua.settings as settings_module
from captua.overlay import OverlayWindow, _deliver_png


def _solid_image(w: int = 64, h: int = 64) -> QImage:
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(QColor("#FF0000"))
    return img


@pytest.fixture()
def win(qapp, tmp_path, monkeypatch):
    """OverlayWindow with a base image and isolated settings."""
    monkeypatch.setattr(settings_module, "CONFIG_DIR", tmp_path / "cfg")
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "cfg" / "settings.json")
    window = OverlayWindow()
    pm = QPixmap(320, 200)
    pm.fill(QColor("#336699"))
    window.set_image(pm)
    yield window
    window._settings["auto_save_on_copy"] = False
    window.close()


class TestDeliverPng:
    def test_encode_and_save(self, tmp_path) -> None:
        target = tmp_path / "sub" / "shot.png"
        ok, name = _deliver_png(_solid_image(), target, use_wl_copy=False)
        assert ok is True
        assert name == "shot.png"
        data = target.read_bytes()
        assert data.startswith(b"\x89PNG")

    def test_save_failure_reports_false(self, tmp_path) -> None:
        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory")
        ok, _ = _deliver_png(_solid_image(), blocker / "shot.png", use_wl_copy=False)
        assert ok is False

    def test_no_save_path_still_succeeds(self) -> None:
        ok, name = _deliver_png(_solid_image(), None, use_wl_copy=False)
        assert ok is True
        assert name == ""


class TestCopyFlow:
    def test_copy_saves_and_closes(self, qtbot, win, tmp_path) -> None:
        win._settings["screenshots_folder"] = str(tmp_path / "shots")
        win.show()
        with qtbot.waitSignal(win.copy_finished, timeout=10000) as blocker:
            win.copy_to_clipboard()
        ok, name = blocker.args
        assert ok is True
        assert name.startswith("captua-")
        saved = list((tmp_path / "shots").glob("captua-*.png"))
        assert len(saved) == 1
        assert saved[0].read_bytes().startswith(b"\x89PNG")
        # Window closed right after successful delivery
        assert not win.isVisible()

    def test_reentrant_copy_is_ignored(self, qtbot, win, tmp_path) -> None:
        win._settings["screenshots_folder"] = str(tmp_path / "shots")
        win._copy_in_progress = True
        win.copy_to_clipboard()  # must be a no-op
        assert not list(tmp_path.glob("shots/*.png"))


class TestEscHierarchy:
    @staticmethod
    def _esc() -> QKeyEvent:
        return QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)

    def test_esc_clears_selection_before_closing(self, qtbot, win) -> None:
        win.show()
        win._view._hide_hint()  # dismiss the first-run hint overlay
        pm = QPixmap(50, 50)
        pm.fill(QColor("#00FF00"))
        item = win._scene.add_image(pm)
        item.setSelected(True)

        win._view.keyPressEvent(self._esc())
        assert win._scene.selectedItems() == []
        assert win.isVisible()  # still open after first Esc

        win._view.keyPressEvent(self._esc())
        assert not win.isVisible()  # second Esc closes


class TestStickyTools:
    def test_tool_finished_switches_to_select_by_default(self, win) -> None:
        win._set_tool("rectangle")
        win._on_tool_finished()
        assert win._toolbar.active_tool() == "select"

    def test_tool_finished_keeps_tool_when_sticky(self, win) -> None:
        win._sticky_tools = True
        win._set_tool("rectangle")
        win._on_tool_finished()
        assert win._toolbar.active_tool() == "rectangle"

    def test_sticky_toggle_updates_flag(self, qtbot, win) -> None:
        with qtbot.waitSignal(win._toolbar.sticky_toggled, timeout=1000) as blocker:
            win._toolbar._sticky_btn.click()
        assert blocker.args == [True]
        assert win._sticky_tools is True


class TestSettingsPersistence:
    def test_close_merges_over_loaded_settings(self, win) -> None:
        win._settings["screenshots_folder"] = "/tmp/custom-shots"
        win._sticky_tools = True
        win.close()
        data = json.loads(settings_module.CONFIG_FILE.read_text())
        assert data["screenshots_folder"] == "/tmp/custom-shots"
        assert data["sticky_tools"] is True
        assert data["update_check_enabled"] is True  # untouched key survives
