"""Regression tests for bugs found in the 2026-10 review."""
import subprocess
from unittest.mock import patch

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QColor, QDropEvent, QImage, QPixmap

from captua.canvas import CanvasScene, CanvasView
from captua.tools import CropTool, ToolProperties


def _scene(qapp, dpr=1.0):
    s = CanvasScene()
    pm = QPixmap(400, 300)
    pm.fill(QColor("red"))
    pm.setDevicePixelRatio(dpr)
    s.set_base_image(pm)
    return s


def test_crop_respects_dpr(qapp):
    s = _scene(qapp, 2.0)
    t = CropTool(s, ToolProperties(), s.history())
    t.mouse_press(None, QPointF(0, 0))
    t.mouse_move(None, QPointF(100, 100))
    t.mouse_release(None, QPointF(100, 100))
    assert s.base_image().pixmap().width() == 200  # 100 logical px * dpr 2


def test_crop_ignores_stray_click(qapp):
    s = _scene(qapp)
    t = CropTool(s, ToolProperties(), s.history())
    t.mouse_press(None, QPointF(10, 10))
    t.mouse_release(None, QPointF(10, 10))
    assert s.base_image().pixmap().width() == 400


def test_drop_local_image_file(qapp, tmp_path):
    path = tmp_path / "a.png"
    img = QImage(10, 10, QImage.Format.Format_ARGB32)
    img.fill(0xFFFF0000)
    img.save(str(path))
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    s = _scene(qapp)
    v = CanvasView(s)
    v.dropEvent(QDropEvent(QPointF(5, 5), Qt.DropAction.CopyAction, mime,
                           Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    assert len(s.image_items()) == 2


def test_self_updater_uses_version_string(qapp):
    from captua.self_updater import SelfUpdater

    with patch.object(SelfUpdater, "_run_pip") as run:
        SelfUpdater("1.2.3").start()
    assert "v1.2.3.tar.gz" in run.call_args[0][0][-1]


def test_load_settings_non_dict(tmp_path, monkeypatch):
    import captua.settings as st

    f = tmp_path / "settings.json"
    f.write_text("[1, 2]")
    monkeypatch.setattr(st, "CONFIG_FILE", f)
    assert st.load_settings() == st._default_settings()


def test_slurp_cancel_is_not_an_error():
    from captua.capture import CaptureCancelled, _run

    done = subprocess.CompletedProcess(["slurp"], 1, "", "selection cancelled\n")
    with patch("subprocess.run", return_value=done):
        with pytest.raises(CaptureCancelled):
            _run(["slurp"], interactive=True)


def test_crop_is_undoable(qapp):
    from captua.items import RectangleItem
    from PySide6.QtCore import QRectF

    s = _scene(qapp)
    rect = RectangleItem(QRectF(5, 5, 20, 20), QColor("blue"), 2, 0)
    s.addItem(rect)
    t = CropTool(s, ToolProperties(), s.history())
    t.mouse_press(None, QPointF(0, 0))
    t.mouse_move(None, QPointF(100, 100))
    t.mouse_release(None, QPointF(100, 100))
    assert s.base_image().pixmap().width() == 100 and rect.scene() is None
    s.history().undo()
    assert s.base_image().pixmap().width() == 400 and rect.scene() is s
    s.history().redo()
    assert s.base_image().pixmap().width() == 100 and rect.scene() is None


def test_redaction_interior_is_opaque(qapp):
    from captua.tools import BlurTool
    from PySide6.QtCore import QRectF

    s = _scene(qapp)
    tool = BlurTool(s, ToolProperties(), s.history())
    pm, _, pad = tool._blur_region(QRectF(50, 50, 80, 60))
    img = pm.toImage()
    # Every pixel inside the selection (even next to its edge) must be fully opaque
    for x, y in [(pad + 1, pad + 1), (pad + 79, pad + 59), (pad + 40, pad + 1)]:
        assert img.pixelColor(x, y).alpha() == 255
