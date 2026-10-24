"""Entry point for Captua."""

import atexit
import os
import signal
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .capture import CaptureCancelled, capture_region, capture_screen, screen_at_cursor
from .settings import load_settings

from . import __version__


def _pid_file() -> Path:
    """Per-user PID file used to enforce the single running instance."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        return Path(runtime) / f"captua-overlay-{os.getuid()}.pid"
    # No runtime dir: a private per-user directory, never a shared /tmp path
    return Path.home() / ".cache" / "captua" / "overlay.pid"


def _is_captua_process(pid: int) -> bool:
    """Guard against killing an unrelated process that recycled the PID."""
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    # Match whole argv entries ("captua" launcher or "-m captua"), not any
    # process that merely mentions the word (editor, pytest, a shell …)
    args = cmdline.split(b"\0")
    return any(a == b"captua" or a.endswith(b"/captua") for a in args) or (
        b"-m" in args and b"captua" in args
    )


def ensure_single_instance() -> bool:
    """Record our PID; return False if another Captua instance is running.

    Repeated key presses must not stack overlays, so a running instance
    wins and the new one exits.
    """
    pid_file = _pid_file()
    try:
        old_pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        old_pid = None

    if old_pid is not None and old_pid != os.getpid() and _is_captua_process(old_pid):
        return False

    try:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(pid_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        atexit.register(lambda: pid_file.unlink(missing_ok=True))
    except OSError:
        pass
    return True


def main() -> int:
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("captua-overlay")
    app.setApplicationDisplayName("Captua")
    app.setDesktopFileName("captua-overlay")
    font = QFont()
    font.setFamilies(["Inter", "Noto Sans", "DejaVu Sans"])
    font.setPointSize(10)
    app.setFont(font)

    # theme reads the system accent at import, so it needs the QApplication first
    from .overlay import OverlayWindow

    # Global tooltip style — bright text on dark background so tooltips are readable
    app.setStyleSheet("""
        QToolTip {
            background-color: #1A1A1A;
            color: #E8E8E8;
            border: 1px solid #2A2A2A;
            padding: 4px 6px;
            border-radius: 4px;
            font-size: 12px;
        }
    """)

    # Choose capture mode from CLI args
    capture_mode = "region"
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--screen", "-s"):
            capture_mode = "screen"
        elif sys.argv[1] in ("--window", "-w"):
            capture_mode = "window"
        elif sys.argv[1] in ("--help", "-h"):
            print("Usage: captua [--screen | -s | --window | -w]")
            print("  (no args)      Select a region with slurp")
            print("  --screen, -s   Capture the full active screen")
            print("  --window, -w   Capture the active window")
            return 0

    if not ensure_single_instance():
        return 0

    try:
        if capture_mode == "region":
            pixmap = capture_region()
        elif capture_mode == "window":
            from .capture import capture_window
            pixmap = capture_window()
        else:
            pixmap = capture_screen()
    except CaptureCancelled:
        return 0
    except RuntimeError as exc:
        print(f"Capture failed: {exc}", file=sys.stderr)
        return 1

    if pixmap is None or pixmap.isNull():
        print("Capture failed: no image was captured", file=sys.stderr)
        return 1

    window = OverlayWindow()

    # Open on the screen under the mouse cursor (or the nearest one, for
    # multi-monitor layouts with gaps between outputs).
    screen = screen_at_cursor()
    if screen is not None:
        window.setScreen(screen)

    window.set_image(pixmap)

    window.show()

    # Async update check (non-blocking, 3-second delay to not interrupt workflow)
    settings = load_settings()
    if settings.get("update_check_enabled", True):
        from .updater import UpdateChecker
        from .update_dialog import UpdateDialog
        from .settings import save_settings

        def _on_update_found(version: str, changelog: str, url: str) -> None:
            skipped = settings.get("skipped_version", "")
            if skipped == version:
                return
            dialog = UpdateDialog(version, changelog, url)
            # Keep a reference: a parentless widget is destroyed once GC'd
            app._update_dialog = dialog
            dialog.skipped.connect(
                lambda v: save_settings({**load_settings(), "skipped_version": v})
            )
            dialog.show()

        checker = UpdateChecker(__version__)
        checker.update_available.connect(_on_update_found)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, checker.check)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
