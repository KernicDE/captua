"""Native screen capture via grim and slurp."""

import json
import subprocess
import tempfile
from pathlib import Path

from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import QApplication


def _set_dpr(pixmap: QPixmap) -> QPixmap:
    """Apply the device-pixel-ratio of the screen under the cursor."""
    try:
        cursor_pos = QCursor.pos()
        for screen in QApplication.screens():
            if screen.geometry().contains(cursor_pos):
                pixmap.setDevicePixelRatio(screen.devicePixelRatio())
                break
        else:
            pixmap.setDevicePixelRatio(QApplication.primaryScreen().devicePixelRatio())
    except Exception:
        pass
    return pixmap


def _trim_border(pixmap: QPixmap) -> QPixmap:
    """Remove a 1 px border that grim sometimes adds on every side."""
    w, h = pixmap.width(), pixmap.height()
    if w > 2 and h > 2:
        return pixmap.copy(1, 1, w - 2, h - 2)
    return pixmap


_TIMEOUT = 15


def _run(cmd: list[str]) -> str:
    """Run a command and return stdout, raising on error."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Command timed out after {_TIMEOUT}s: {' '.join(cmd)}") from exc
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def capture_region() -> QPixmap:
    """Prompt user to select a region with slurp, capture it with grim."""
    geometry = _run(["slurp"])
    if not geometry:
        raise RuntimeError("No region selected")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _run(["grim", "-c", "-g", geometry, tmp_path])
        return _trim_border(_set_dpr(QPixmap(tmp_path)))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def capture_screen() -> QPixmap:
    """Capture the full active screen."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _run(["grim", "-c", tmp_path])
        return _trim_border(_set_dpr(QPixmap(tmp_path)))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def capture_window() -> QPixmap:
    """Capture the currently focused Hyprland window."""
    try:
        result = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"hyprctl timed out after {_TIMEOUT}s") from exc
    if result.returncode != 0:
        raise RuntimeError(f"hyprctl failed: {result.stderr}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"hyprctl returned invalid JSON: {result.stdout!r}") from exc
    at = data.get("at", [0, 0])
    size = data.get("size", [0, 0])
    scale = data.get("scale", 1.0)

    if size[0] == 0 or size[1] == 0:
        raise RuntimeError("No active window found")

    geometry = f"{at[0]},{at[1]} {size[0]}x{size[1]}"

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _run(["grim", "-c", "-g", geometry, tmp_path])
        pixmap = _trim_border(QPixmap(tmp_path))
        pixmap.setDevicePixelRatio(float(scale))
        return pixmap
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def copy_pixmap_to_clipboard(pixmap: QPixmap) -> None:
    """Copy a QPixmap to the Wayland clipboard via wl-copy."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        pixmap.save(tmp_path, "PNG")
        subprocess.run(
            ["wl-copy", "--type", "image/png"],
            input=Path(tmp_path).read_bytes(),
            check=True,
            timeout=_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"wl-copy timed out after {_TIMEOUT}s") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)
