"""Tests for the Litterbox uploader."""
import pytest

from captua.settings import _sanitize, _default_settings
from captua.uploader import parse_link


@pytest.mark.parametrize("text", [
    "https://litterbox.catbox.moe/abc123.png\n",
    "https://files.catbox.moe/abc123.png",
    "https://litter.catbox.moe/53zml6.png",
])
def test_parse_link_accepts_service_hosts(text):
    assert parse_link(text) == text.strip()


@pytest.mark.parametrize("text", [
    "", "Error: file too large", "http://litterbox.catbox.moe/a.png",
    "https://evil.example/a.png", "https://litterbox.catbox.moe.evil.example/a.png",
])
def test_parse_link_rejects_everything_else(text):
    assert parse_link(text) is None


def test_invalid_expiry_falls_back_to_default():
    d = _default_settings()
    assert _sanitize({**d, "upload_expiry": "forever"}, d)["upload_expiry"] == "24h"
    assert _sanitize({**d, "upload_expiry": "1h"}, d)["upload_expiry"] == "1h"


def test_overlay_upload_flow(qapp, tmp_path, monkeypatch):
    """Consent is asked once for temporary uploads, always for permanent ones; the link lands in the clipboard."""
    from PySide6.QtGui import QColor, QPixmap
    from PySide6.QtWidgets import QApplication, QMessageBox

    import captua.settings as settings_module
    from captua.overlay import OverlayWindow

    monkeypatch.setattr(settings_module, "CONFIG_DIR", tmp_path / "cfg")
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "cfg" / "settings.json")
    asked, sent = [], []
    monkeypatch.setattr(QMessageBox, "question", lambda *a: asked.append(a[2]) or QMessageBox.StandardButton.Yes)
    win = OverlayWindow()
    pm = QPixmap(40, 30)
    pm.fill(QColor("#336699"))
    win.set_image(pm)
    monkeypatch.setattr(win._uploader, "upload", lambda png, expiry: sent.append((png[:4], expiry)))

    win.upload_image()
    win._on_upload_finished("https://litter.catbox.moe/x.png")
    win.upload_image()  # consent remembered
    win._on_upload_finished("https://litter.catbox.moe/x.png")
    win.upload_image(permanent=True)  # asks again
    assert len(asked) == 2 and "permanently" in asked[1]
    assert [e for _, e in sent] == ["24h", "24h", "permanent"]
    assert sent[0][0] == b"\x89PNG"
    win._on_upload_finished("https://files.catbox.moe/y.png")
    assert QApplication.clipboard().text() == "https://files.catbox.moe/y.png"
    win._settings["auto_save_on_copy"] = False
    win.close()
