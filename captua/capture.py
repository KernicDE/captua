"""Native screen capture via grim and slurp."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from PySide6.QtGui import QCursor, QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication


def nearest_screen(pos):
    """Screen whose geometry is closest to pos (0 if pos is inside it).

    Multi-monitor layouts can have gaps between screens (e.g. outputs at
    different y-offsets, as with a rotated side monitor); if the cursor
    sits in such a gap, neither geometry().contains() nor
    QGuiApplication.screenAt() matches any screen. Falling back to the
    nearest one instead of "no screen" avoids grim defaulting to every
    connected output combined into one oversized image.
    """
    screens = QApplication.screens()
    if not screens:
        return None

    def _distance(screen) -> int:
        rect = screen.geometry()
        dx = max(rect.left() - pos.x(), 0, pos.x() - rect.right())
        dy = max(rect.top() - pos.y(), 0, pos.y() - rect.bottom())
        return dx * dx + dy * dy

    return min(screens, key=_distance)


def screen_at_cursor():
    """Screen under the cursor, falling back to the nearest / primary one."""
    try:
        cursor_pos = QCursor.pos()
        return (
            QGuiApplication.screenAt(cursor_pos)
            or nearest_screen(cursor_pos)
            or QApplication.primaryScreen()
        )
    except Exception:
        return QApplication.primaryScreen()


def _set_dpr(pixmap: QPixmap) -> QPixmap:
    """Apply the device-pixel-ratio of the screen under the cursor."""
    screen = screen_at_cursor()
    if screen is not None:
        pixmap.setDevicePixelRatio(screen.devicePixelRatio())
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
    """Prompt user to select a region and capture it."""
    if _is_kde():
        return _capture_region_kde()

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
    """Capture the full active screen (the one under the cursor).

    Without -o, grim captures every connected output combined into one
    oversized image spanning the whole virtual desktop.
    """
    if _is_kde():
        return _capture_screen_kde()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    screen = screen_at_cursor()
    cmd = ["grim", "-c"]
    if screen is not None:
        cmd += ["-o", screen.name()]
    cmd.append(tmp_path)

    try:
        _run(cmd)
        return _trim_border(_set_dpr(QPixmap(tmp_path)))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _is_niri() -> bool:
    """Check whether Niri is the current compositor."""
    return os.environ.get("XDG_CURRENT_DESKTOP", "").lower() == "niri"


def _is_kde() -> bool:
    """Check whether KDE Plasma (KWin) is the current desktop.

    KWin does not implement the wlr-screencopy protocol grim/slurp rely on,
    so region/screen/window capture shell out to Spectacle's CLI instead.
    """
    return "kde" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()


def _spectacle_capture(*flag: str) -> QPixmap:
    """Run Spectacle in background mode with the given mode flag, load the result."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _run(["spectacle", "-b", "-n", *flag, "-o", tmp_path])
        if not Path(tmp_path).exists() or Path(tmp_path).stat().st_size == 0:
            raise RuntimeError("Spectacle did not produce a screenshot")
        return _set_dpr(QPixmap(tmp_path))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _capture_region_kde() -> QPixmap:
    """Capture an interactively selected region via Spectacle."""
    return _spectacle_capture("-r")


def _capture_screen_kde() -> QPixmap:
    """Capture the current screen (the one under the cursor) via Spectacle."""
    return _spectacle_capture("-m")


def _capture_window_kde() -> QPixmap:
    """Capture the active window via Spectacle."""
    return _spectacle_capture("-a")


def capture_window() -> QPixmap:
    """Capture the currently focused window (Hyprland, Niri, or KDE/KWin)."""
    if _is_niri():
        return _capture_window_niri()
    if _is_kde():
        return _capture_window_kde()
    return _capture_window_hyprland()


def _capture_window_niri() -> QPixmap:
    """Capture the focused window under Niri.

    Niri does not expose window absolute coordinates, so we let Niri take the
    screenshot and then load the most recent file from the screenshots dir.
    """
    screenshots_dir = Path.home() / "Pictures" / "Screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Find the newest screenshot before Niri writes a new one.
    before = max(
        (p.stat().st_mtime for p in screenshots_dir.glob("*.png")),
        default=0,
    )

    _run(["niri", "msg", "action", "screenshot-window"])

    # Wait briefly for the file to appear.
    new_path: Path | None = None
    for _ in range(50):
        candidates = [
            p for p in screenshots_dir.glob("*.png")
            if p.stat().st_mtime > before
        ]
        if candidates:
            new_path = max(candidates, key=lambda p: p.stat().st_mtime)
            break
        import time
        time.sleep(0.05)

    if new_path is None:
        raise RuntimeError("Niri did not write a screenshot file")

    return _trim_border(_set_dpr(QPixmap(str(new_path))))


def _capture_window_hyprland() -> QPixmap:
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
