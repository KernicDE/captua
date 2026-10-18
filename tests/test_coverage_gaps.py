import json

import pytest
from PySide6.QtCore import QPointF, QRectF, QJsonValue
from PySide6.QtGui import QColor, QPixmap

import captua.settings as settings_module
from captua.canvas import CanvasScene
from captua.tools import CropTool, ToolProperties


def _scene(dpr=1.0):
    s = CanvasScene()
    pm = QPixmap(400, 300)
    pm.fill(QColor("red"))
    pm.setDevicePixelRatio(dpr)
    s.set_base_image(pm)
    return s


def _drag(s, a, b):
    t = CropTool(s, ToolProperties(), s.history())
    t.mouse_press(None, QPointF(*a))
    t.mouse_move(None, QPointF(*b))
    t.mouse_release(None, QPointF(*b))


# 1. updater
class _Reply:
    def __init__(self, payload: bytes, ok=True):
        self._p, self._ok = payload, ok
    def error(self):
        from PySide6.QtNetwork import QNetworkReply
        return QNetworkReply.NetworkError.NoError if self._ok else QNetworkReply.NetworkError.HostNotFoundError
    def errorString(self):
        return "boom"
    def readAll(self):
        from PySide6.QtCore import QByteArray
        return QByteArray(self._p)


@pytest.mark.parametrize("latest,current,newer", [
    ("0.7.2", "0.7.1", True), ("0.7.1", "0.7.1", False), ("0.7.0", "0.7.1", False),
    ("0.10.0", "0.9.0", True), ("1.0", "0.9.9", True), ("0.7.1.1", "0.7.1", True),
])
def test_is_newer_compares_numerically(latest, current, newer):
    from captua.updater import UpdateChecker
    assert UpdateChecker._is_newer(latest, current) is newer


@pytest.mark.parametrize("tag,expect", [
    ("v0.8.0", "update"), ("v0.7.1", "none"), ("latest", "error"),
    ("v1.2.3-rc1", "error"), ("v1.2; rm -rf", "error"), ("", "error"),
])
def test_updater_tag_validation(qapp, tag, expect):
    from captua.updater import UpdateChecker
    u = UpdateChecker("0.7.1")
    seen = []
    u.update_available.connect(lambda *a: seen.append("update"))
    u.no_update.connect(lambda: seen.append("none"))
    u.error.connect(lambda m: seen.append("error"))
    u._on_reply(_Reply(json.dumps({"tag_name": tag, "body": "b", "html_url": "u"}).encode()))
    assert seen == [expect]


# 2. crop offset with dpr
def test_crop_offset_and_size_scale_with_dpr(qapp):
    s = _scene(2.0)
    base_pm = s.base_image().pixmap()
    from PySide6.QtGui import QPainter
    p = QPainter(base_pm); p.fillRect(50, 30, 20, 20, QColor("blue")); p.end()  # logical coords -> device (100,60,40,40)
    s.base_image().setPixmap(base_pm)
    _drag(s, (50, 30), (90, 70))  # logical -> device (100,60,80,80)
    out = s.base_image().pixmap()
    assert (out.width(), out.height()) == (80, 80) and out.devicePixelRatio() == 2.0
    assert out.toImage().pixelColor(0, 0) == QColor("blue")  # offset multiplied by dpr
    assert out.toImage().pixelColor(39, 39) == QColor("blue")


def test_crop_threshold_is_per_axis(qapp):
    s = _scene()
    _drag(s, (10, 10), (200, 14))  # wide but only 4px tall
    assert s.base_image().pixmap().height() == 300


# 3. CropCommand.undo restores image-item registry
def test_crop_undo_restores_image_items_registry(qapp):
    s = _scene()
    extra = QPixmap(50, 50); extra.fill(QColor("green"))
    s.add_image(extra, QPointF(150, 150))
    before = list(s._image_items)
    _drag(s, (0, 0), (100, 100))
    assert s._image_items == []
    s.history().undo()
    assert s._image_items == before and len(before) == 1
    s.history().redo(); s.history().undo()
    assert s._image_items == before


# 4. close keeps skipped_version written while window open
def test_close_keeps_skipped_version_written_while_open(qapp, tmp_path, monkeypatch):
    from captua.overlay import OverlayWindow
    monkeypatch.setattr(settings_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "settings.json")
    w = OverlayWindow()
    pm = QPixmap(100, 100); pm.fill(QColor("red")); w.set_image(pm)
    w._settings["auto_save_on_copy"] = False
    settings_module.save_settings({**settings_module.load_settings(), "skipped_version": "9.9.9"})
    w.close()
    assert json.loads(settings_module.CONFIG_FILE.read_text())["skipped_version"] == "9.9.9"


# 5. Stepper edges
def _stepper():
    from captua.toolbar import Stepper
    return Stepper([1, 2, 3], lambda v: f"{v:g}", "t")


def test_stepper_clamps_and_disables_buttons_at_ends(qapp):
    st = _stepper(); got = []
    st.value_changed.connect(got.append)
    st.set_value(3)
    assert not st._plus.isEnabled() and st._minus.isEnabled()
    st._move(1); assert st.value() == 3 and got == []
    st.set_value(1)
    assert not st._minus.isEnabled() and st._plus.isEnabled()
    st._move(-1); assert st.value() == 1 and got == []


@pytest.mark.parametrize("text,val,emits", [("2x", 2, [2]), ("2.4", 2, [2]), ("garbage", 3, []), ("1", 1, [1])])
def test_stepper_typed_text(qapp, text, val, emits):
    st = _stepper(); st.set_value(3 if text == "garbage" else 1 if text == "1" else 3)
    if text == "1": st.set_value(3)
    got = []; st.value_changed.connect(got.append)
    st._edit.setText(text); st._on_edit()
    assert st.value() == val and got == emits
