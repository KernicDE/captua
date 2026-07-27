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

from .capture import capture_region, capture_screen, screen_at_cursor
from .overlay import OverlayWindow
from .settings import load_settings

from . import __version__


def _pid_file() -> Path:
    """Per-user PID file used to enforce the single running instance."""
    runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return Path(runtime) / f"captua-overlay-{os.getuid()}.pid"


def _is_captua_process(pid: int) -> bool:
    """Guard against killing an unrelated process that recycled the PID."""
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    return b"captua" in cmdline


def ensure_single_instance() -> None:
    """Terminate a previously running Captua instance and record our PID.

    Captua is a one-shot annotation overlay: starting a new capture means
    the old overlay is stale, so it gets a SIGTERM (with a short grace
    period) before the new instance takes over.
    """
    pid_file = _pid_file()
    old_pid: int | None = None
    try:
        old_pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pass

    if old_pid is not None and old_pid != os.getpid() and _is_captua_process(old_pid):
        try:
            os.kill(old_pid, signal.SIGTERM)
            for _ in range(20):  # up to 2 s grace period
                time.sleep(0.1)
                try:
                    os.kill(old_pid, 0)
                except OSError:
                    break
        except OSError:
            pass

    try:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
        atexit.register(lambda: pid_file.unlink(missing_ok=True))
    except OSError:
        pass


def main() -> int:
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("captua-overlay")
    app.setApplicationDisplayName("Captua")
    app.setDesktopFileName("captua-overlay")
    app.setFont(QFont("Inter", 10))

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
            print("  --window, -w   Capture the active Hyprland window")
            return 0

    # A new capture replaces any still-open overlay from a previous run
    ensure_single_instance()

    try:
        if capture_mode == "region":
            pixmap = capture_region()
        elif capture_mode == "window":
            from .capture import capture_window
            pixmap = capture_window()
        else:
            pixmap = capture_screen()
    except RuntimeError as exc:
        print(f"Capture failed: {exc}", file=sys.stderr)
        return 1

    window = OverlayWindow()

    # Open on the screen under the mouse cursor (or the nearest one, for
    # multi-monitor layouts with gaps between outputs).
    screen = screen_at_cursor()
    if screen is not None:
        window.setScreen(screen)

    if pixmap is not None and not pixmap.isNull():
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
            dialog.skipped.connect(lambda v: save_settings({**settings, "skipped_version": v}))
            dialog.show()

        checker = UpdateChecker(__version__)
        checker.update_available.connect(_on_update_found)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, checker.check)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
