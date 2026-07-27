"""Scripted captua demo: opens the overlay with a mock app screenshot and
performs a timed sequence of annotation actions for screen recording.

Usage (Wayland session, repo as PYTHONPATH):
    python3 scripts/make_demo_image.py
    QT_QPA_PLATFORM=wayland PYTHONPATH=. python3 scripts/record_demo.py &
    # grab the window geometry (niri msg windows, title "captua-demo"), then
    gpu-screen-recorder -w "990x703+X+Y" -f 30 -c mp4 -o /tmp/captua-demo.mp4
The scripted run finishes with a copy (window closes) after ~15 s.
"""

import sys

from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import QApplication

from captua.capture import screen_at_cursor
from captua.overlay import OverlayWindow


def mouse(view, etype, vp_pos, button=Qt.MouseButton.LeftButton, buttons=None):
    if buttons is None:
        buttons = button if etype != QEvent.Type.MouseButtonRelease else Qt.MouseButton.NoButton
    ev = QMouseEvent(etype, QPointF(vp_pos), QPointF(vp_pos), button, buttons,
                     Qt.KeyboardModifier.NoModifier)
    if etype == QEvent.Type.MouseButtonPress:
        view.mousePressEvent(ev)
    elif etype == QEvent.Type.MouseMove:
        view.mouseMoveEvent(ev)
    else:
        view.mouseReleaseEvent(ev)


class Demo:
    def __init__(self, win: OverlayWindow) -> None:
        self.win = win
        self.view = win._view
        self._schedule: list[tuple[int, object]] = []

    def at(self, ms: int, fn) -> None:
        QTimer.singleShot(ms, fn)

    def vp(self, sx: float, sy: float) -> QPointF:
        """Scene coords -> viewport coords."""
        return self.view.mapFromScene(QPointF(sx, sy))

    def tool(self, ms: int, name: str) -> None:
        self.at(ms, lambda: self.win._toolbar.set_tool(name))

    def drag(self, ms: int, p1: tuple, p2: tuple, steps: int = 12, step_ms: int = 70) -> int:
        """Simulate a left-drag from scene p1 to p2. Returns end time."""
        self.at(ms, lambda: mouse(self.view, QEvent.Type.MouseButtonPress, self.vp(*p1)))
        for i in range(1, steps + 1):
            x = p1[0] + (p2[0] - p1[0]) * i / steps
            y = p1[1] + (p2[1] - p1[1]) * i / steps
            self.at(ms + i * step_ms, lambda x=x, y=y: mouse(self.view, QEvent.Type.MouseMove, self.vp(x, y)))
        end = ms + (steps + 1) * step_ms
        self.at(end, lambda: mouse(self.view, QEvent.Type.MouseButtonRelease, self.vp(*p2)))
        return end

    def click(self, ms: int, p: tuple) -> None:
        self.at(ms, lambda: mouse(self.view, QEvent.Type.MouseButtonPress, self.vp(*p)))
        self.at(ms + 120, lambda: mouse(self.view, QEvent.Type.MouseButtonRelease, self.vp(*p)))

    def type_text(self, ms: int, text: str, char_ms: int = 80) -> int:
        key_map = {" ": Qt.Key.Key_Space}
        for i, ch in enumerate(text):
            key = key_map.get(ch, getattr(Qt.Key, f"Key_{ch.upper()}", Qt.Key.Key_unknown))
            self.at(ms + i * char_ms, lambda ch=ch, key=key: self.view.keyPressEvent(
                QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, ch)))
        return ms + len(text) * char_ms

    def esc(self, ms: int) -> None:
        self.at(ms, lambda: self.view.keyPressEvent(
            QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("captua-overlay")
    app.setDesktopFileName("captua-overlay")

    win = OverlayWindow()
    screen = screen_at_cursor()
    if screen is not None:
        win.setScreen(screen)
    win.set_image(QPixmap("/tmp/demo-app.png"))
    win._settings["auto_save_on_copy"] = False  # don't clutter ~/Pictures
    # Brand-consistent annotations regardless of user settings
    from PySide6.QtGui import QColor
    win._props.color = QColor("#FF5D62")
    win._props.fill_color = QColor("#FF5D62")
    win._props.stroke_width = 4
    win._toolbar.set_line_color(win._props.color)
    win._toolbar.set_fill_color(win._props.fill_color)
    win._toolbar.set_line_width(4)
    win.show()
    win.setWindowTitle("captua-demo")

    d = Demo(win)

    # 1) Rectangle around "Now Playing"
    d.tool(2500, "rectangle")
    d.drag(2900, (240, 78), (838, 232))

    # 2) Arrow from track row to the Copy button
    d.tool(4300, "arrow")
    d.drag(4700, (575, 300), (770, 492))

    # 3) Counter badges on the first three tracks
    d.tool(6000, "counter")
    d.click(6300, (260, 258))
    d.click(6800, (260, 298))
    d.click(7300, (260, 338))

    # 4) Text annotation
    d.tool(8000, "text")
    d.click(8300, (400, 52))
    end_type = d.type_text(8600, "neues album")
    d.at(end_type + 300, lambda: win._scene.clearFocus())

    # 5) Blur the API token
    d.tool(10500, "blur")
    d.drag(10900, (250, 426), (828, 470))

    # Final state, then copy (window closes instantly)
    d.tool(12500, "select")
    d.at(14500, win.copy_to_clipboard)

    QTimer.singleShot(17000, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
