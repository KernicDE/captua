"""Fullscreen region selector overlay that runs before the editor opens."""

from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPixmap, QColor, QPen, QKeyEvent
from PySide6.QtWidgets import QWidget


class RegionSelector(QWidget):
    """
    A frameless fullscreen widget that shows the captured screenshot
    and lets the user drag to select a region.

    DEPRECATED: On Wayland this approach is unreliable.  Use ``slurp``
    instead (see ``capture.py``).
    """

    selection_finished = Signal(QRect)
    selection_cancelled = Signal()

    def __init__(self, pixmap: QPixmap, parent=None) -> None:
        super().__init__(parent)
        self._pixmap = pixmap
        self._start = None
        self._current = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(pixmap.width(), pixmap.height())
        self.setCursor(Qt.CursorShape.CrossCursor)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)

        if self._start and self._current:
            rect = QRect(self._start, self._current).normalized()

            # Dim outside
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 140))
            w, h = self.width(), self.height()
            painter.drawRect(0, 0, w, rect.top())
            painter.drawRect(0, rect.bottom(), w, h - rect.bottom())
            painter.drawRect(0, rect.top(), rect.left(), rect.height())
            painter.drawRect(rect.right(), rect.top(), w - rect.right(), rect.height())

            # Border
            painter.setPen(QPen(QColor("#7E9CD8"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrick)
            painter.drawRect(rect)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._current = event.pos()
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.selection_cancelled.emit()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._start is not None:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._start is not None:
            rect = QRect(self._start, event.pos()).normalized()
            self._start = None
            self._current = None
            if rect.width() > 2 and rect.height() > 2:
                self.selection_finished.emit(rect)
            else:
                self.selection_cancelled.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.selection_cancelled.emit()
        else:
            super().keyPressEvent(event)
