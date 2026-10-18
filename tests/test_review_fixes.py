"""Regression tests for the 0.7.2 review fixes."""
import os
import stat
import sys

import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QImage, QPixmap

from captua.canvas import CanvasScene
from captua.history import push_changes, snapshot
from captua.items import MagnifierCalloutItem, RectangleItem, TextItem, render_region


def _scene(w=100, h=80, dpr=1.0):
    s = CanvasScene()
    pm = QPixmap(round(w * dpr), round(h * dpr))
    pm.fill(QColor("blue"))
    pm.setDevicePixelRatio(dpr)
    s.set_base_image(pm)
    return s


def test_base_image_bounding_rect_is_exact(qapp):
    s = _scene(40, 40)
    assert s.base_image().boundingRect() == QRectF(0, 0, 40, 40)


def test_export_has_no_blank_edge(qapp):
    from captua.overlay import OverlayWindow

    w = OverlayWindow()
    pm = QPixmap(40, 40)
    pm.fill(QColor("red"))
    w.set_image(pm)
    w._scene.backdrop_enabled = False
    w._scene.base_image().set_corner_radius(0)
    out = w.render_to_pixmap().toImage()
    assert (out.width(), out.height()) == (40, 40)
    assert out.pixelColor(39, 39) == QColor("red")


def test_move_is_undoable(qapp):
    s = _scene()
    rect = RectangleItem(QRectF(10, 10, 20, 20), QColor("red"), 2, 0)
    s.addItem(rect)
    before = snapshot(s)
    rect.setPos(QPointF(30, 5))
    assert push_changes(s, before)
    s.history().undo()
    assert rect.pos() == QPointF(0, 0)
    s.history().redo()
    assert rect.pos() == QPointF(30, 5)
    assert not push_changes(s, snapshot(s))  # unchanged -> no command


def test_style_change_is_undoable(qapp):
    s = _scene()
    rect = RectangleItem(QRectF(10, 10, 20, 20), QColor("red"), 2, 0)
    s.addItem(rect)
    before = snapshot(s)
    rect.set_line_width(9)
    push_changes(s, before)
    s.history().undo()
    assert rect.line_width() == 2


def test_added_image_undo_and_registry(qapp):
    s = _scene()
    extra = QPixmap(30, 30)
    extra.fill(QColor("green"))
    item = s.add_image(extra, QPointF(50, 50))
    assert item in s._image_items
    s.history().undo()
    assert item not in s._image_items and item.scene() is None
    s.history().redo()
    assert item in s._image_items and item.scene() is s


def test_magnifier_watcher_survives_undo_redo(qapp):
    s = _scene()
    mag = MagnifierCalloutItem(QPointF(30, 30), 10, QPointF(70, 30), 20, QPixmap(10, 10), 2.0)
    s.addItem(mag)
    s.removeItem(mag)
    mag._pos_watcher._check()
    s.addItem(mag)
    assert mag._pos_watcher._timer.isActive()


def test_magnifier_geometry_roundtrip(qapp):
    s = _scene()
    mag = MagnifierCalloutItem(QPointF(30, 30), 10, QPointF(70, 30), 20, QPixmap(10, 10), 2.0)
    s.addItem(mag)
    state = mag.geometry_state()
    mag.set_src_radius(25, rebuild=False)
    mag.restore_geometry(*state)
    assert mag._src_r == 10 and mag._dest_r == 20


def test_empty_text_item_is_dropped(qapp):
    s = _scene()
    from captua.history import AddItemCommand

    item = TextItem(QPointF(5, 5), QColor("red"))
    s.addItem(item)
    s.history().push(AddItemCommand(s, item))
    item.clearFocus()
    from PySide6.QtGui import QFocusEvent
    from PySide6.QtCore import Qt

    item.focusOutEvent(QFocusEvent(QFocusEvent.Type.FocusOut, Qt.FocusReason.OtherFocusReason))
    assert item.scene() is None and not s.history().can_undo()


def test_render_region_scales_with_dpr(qapp):
    s = _scene(100, 80, dpr=2.0)
    pm = render_region(s, QRectF(10, 10, 20, 10))
    assert (pm.width(), pm.height()) == (40, 20)
    assert pm.devicePixelRatio() == 2.0


def test_blur_covers_selection_at_dpr2_and_edge(qapp):
    from captua.history import History
    from captua.tools import BlurTool, ToolProperties

    s = _scene(100, 80, dpr=2.0)
    tool = BlurTool(s, ToolProperties(), History())
    blurred, offset, pad = tool._blur_region(QRectF(0, 0, 30, 30))  # touches the top-left edge
    assert blurred.devicePixelRatio() == 2.0
    assert offset == QPointF(-pad, -pad)
    img = blurred.toImage()
    # inside the selection (starting at pad logical px) the result is fully opaque
    assert img.pixelColor(round((pad + 5) * 2), round((pad + 5) * 2)).alpha() == 255


def test_load_image_file_rejects_non_images(qapp, tmp_path):
    from captua.imageio import load_image_file

    good = tmp_path / "a.png"
    QImage(4, 4, QImage.Format.Format_RGB32).save(str(good))
    assert load_image_file(str(good)) is not None
    text = tmp_path / "b.png"
    text.write_text("not an image")
    assert load_image_file(str(text)) is None
    fifo = tmp_path / "c.png"
    os.mkfifo(fifo)
    assert load_image_file(str(fifo)) is None  # must not block on a FIFO
    assert load_image_file(str(tmp_path / "missing.png")) is None


def test_settings_bad_types_fall_back(tmp_path, monkeypatch):
    import json

    import captua.settings as sm

    monkeypatch.setattr(sm, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(sm, "CONFIG_FILE", tmp_path / "settings.json")
    (tmp_path / "settings.json").write_text(json.dumps({
        "screenshots_folder": 5, "backdrop_padding": 10**9, "line_color": "nope",
        "snap_enabled": "yes", "fill_alpha": 100,
    }))
    s = sm.load_settings()
    d = sm._default_settings()
    assert s["screenshots_folder"] == d["screenshots_folder"]
    assert s["backdrop_padding"] == d["backdrop_padding"]
    assert s["line_color"] == d["line_color"]
    assert s["snap_enabled"] is True
    assert s["fill_alpha"] == 100


def test_auto_save_never_overwrites(tmp_path):
    from captua.overlay import _write_new_file

    p = tmp_path / "shot.png"
    assert _write_new_file(p, b"1") == p
    assert _write_new_file(p, b"2") == tmp_path / "shot-2.png"
    assert p.read_bytes() == b"1"
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    link = tmp_path / "link.png"
    link.symlink_to(tmp_path / "target.png")  # dangling link must not be followed
    out = _write_new_file(link, b"3")
    assert out != link and not (tmp_path / "target.png").exists()


def test_updater_url_comes_from_tag_and_notes_are_capped(qapp):
    import json

    from PySide6.QtCore import QByteArray
    from PySide6.QtNetwork import QNetworkReply

    from captua.updater import _MAX_NOTES, UpdateChecker

    class R:
        def error(self): return QNetworkReply.NetworkError.NoError
        def readAll(self): return QByteArray(json.dumps(
            {"tag_name": "v9.0.0", "body": "x" * (_MAX_NOTES * 2), "html_url": "file:///etc/passwd"}).encode())

    u = UpdateChecker("0.7.1")
    got = []
    u.update_available.connect(lambda v, body, url: got.append((v, len(body), url)))
    u._on_reply(R())
    assert got == [("9.0.0", _MAX_NOTES, "https://github.com/KernicDE/captua/releases/tag/v9.0.0")]


def test_restart_uses_isolated_python(monkeypatch):
    from captua import self_updater

    calls = {}
    monkeypatch.setattr(self_updater.os, "chdir", lambda p: calls.setdefault("cwd", str(p)))
    monkeypatch.setattr(self_updater.os, "execl", lambda *a: calls.setdefault("argv", a))
    self_updater.SelfUpdater.restart()
    argv = list(calls["argv"])
    assert argv[2:5] == ["-P", "-m", "captua"]
    assert calls["cwd"] != "/tmp"


def test_main_module_exists():
    import importlib.util

    assert importlib.util.find_spec("captua.__main__") is not None


def test_pid_check_matches_argv_not_substrings(monkeypatch):
    import captua.main as m
    from pathlib import Path

    def fake(cmdline):
        monkeypatch.setattr(Path, "read_bytes", lambda self: cmdline)
        return m._is_captua_process(1)

    assert fake(b"/usr/bin/python\0/home/u/.local/bin/captua\0")
    assert fake(b"python\0-m\0captua\0")
    assert not fake(b"vim\0/home/u/Development/captua/x.py\0")
    assert not fake(b"pytest\0captua_tests\0")


def test_toolbar_style_change_on_selection_is_one_undo_step(qapp):
    from captua.overlay import OverlayWindow

    w = OverlayWindow()
    pm = QPixmap(100, 100)
    pm.fill(QColor("blue"))
    w.set_image(pm)
    rect = RectangleItem(QRectF(10, 10, 20, 20), QColor("red"), 2, 0)
    w._scene.addItem(rect)
    rect.setSelected(True)
    w._update_line_width(9)
    assert rect.line_width() == 9
    w._scene.history().undo()
    assert rect.line_width() == 2


def test_magnifier_zoom_change_is_undoable(qapp):
    from captua.overlay import OverlayWindow

    w = OverlayWindow()
    pm = QPixmap(200, 200)
    pm.fill(QColor("blue"))
    w.set_image(pm)
    mag = MagnifierCalloutItem(QPointF(50, 50), 10, QPointF(120, 50), 20, QPixmap(10, 10), 2.0)
    w._scene.addItem(mag)
    mag.setSelected(True)
    w._update_magnifier_zoom(4.0)
    assert mag.zoom_level() == 4.0
    w._scene.history().undo()
    assert mag.zoom_level() == 2.0 and mag._dest_r == 20
