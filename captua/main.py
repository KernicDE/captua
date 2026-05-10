"""Entry point for Captua."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import QApplication

from .capture import capture_region, capture_screen
from .overlay import OverlayWindow


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
            background-color: #2A2A37;
            color: #DCD7BA;
            border: 1px solid #54546D;
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

    # Open on the screen that currently contains the mouse cursor
    cursor_pos = QCursor.pos()
    for screen in app.screens():
        if screen.geometry().contains(cursor_pos):
            window.setScreen(screen)
            break

    if pixmap is not None and not pixmap.isNull():
        window.set_image(pixmap)

    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
