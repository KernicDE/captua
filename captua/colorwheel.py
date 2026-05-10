"""HSL colour disc picker dialog."""

import math

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class _ColorDisc(QWidget):
    color_changed = Signal(QColor)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._hue = 0.0
        self._saturation = 1.0
        self._lightness = 0.5
        self._inverted = True  # True: white centre → black rim (default)
        self._cached: QImage | None = None
        self.setFixedSize(240, 240)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _center(self) -> QPoint:
        return QPoint(self.width() // 2, self.height() // 2)

    def _radius(self) -> int:
        return min(self.width(), self.height()) // 2 - 4

    def _render_disc(self) -> QImage:
        size = self.width()
        img = QImage(size, size, QImage.Format.Format_ARGB32)
        cx, cy = size // 2, size // 2
        radius = self._radius()
        s = self._saturation
        inv = self._inverted

        for y in range(size):
            for x in range(size):
                dx = x - cx
                dy = y - cy
                dist = math.hypot(dx, dy)
                if dist > radius:
                    img.setPixelColor(x, y, QColor(0, 0, 0, 0))
                    continue

                angle = math.atan2(-dy, dx)
                hue = ((angle / (2 * math.pi)) + 1.0) % 1.0
                l = dist / radius
                if inv:
                    l = 1.0 - l
                img.setPixelColor(x, y, QColor.fromHslF(hue, s, l))

        return img

    def color(self) -> QColor:
        return QColor.fromHslF(self._hue, self._saturation, self._lightness)

    def set_color(self, color: QColor) -> None:
        h, s, l, _ = color.getHslF()
        self._hue = h if h >= 0 else 0.0
        self._saturation = s
        self._lightness = l
        self._cached = None
        self.update()

    def set_saturation(self, s: float) -> None:
        self._saturation = max(0.0, min(1.0, s))
        self._cached = None
        self.update()
        self.color_changed.emit(self.color())

    def set_inverted(self, inv: bool) -> None:
        self._inverted = inv
        self._cached = None
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._cached is None or self._cached.size() != self.size():
            self._cached = self._render_disc()

        painter.drawImage(0, 0, self._cached)

        # indicator
        cx, cy = self._center().x(), self._center().y()
        radius = self._radius()
        angle = self._hue * 2 * math.pi
        l = 1.0 - self._lightness if self._inverted else self._lightness
        r = l * radius
        ix = int(cx + r * math.cos(angle))
        iy = int(cy - r * math.sin(angle))

        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(ix - 5, iy - 5, 10, 10)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._update_from_pos(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._update_from_pos(event.pos())

    def _update_from_pos(self, pos: QPoint) -> None:
        cx, cy = self._center().x(), self._center().y()
        dx = pos.x() - cx
        dy = pos.y() - cy
        angle = math.atan2(-dy, dx)
        self._hue = ((angle / (2 * math.pi)) + 1.0) % 1.0
        dist = math.hypot(dx, dy)
        radius = self._radius()
        l = max(0.0, min(1.0, dist / radius))
        self._lightness = 1.0 - l if self._inverted else l
        self.update()
        self.color_changed.emit(self.color())


_DIALOG_STYLE = """
    QDialog {
        background-color: #16161D;
    }
    QPushButton {
        background-color: #2A2A37;
        color: #DCD7BA;
        border: 1px solid #54546D;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #363646;
        border: 1px solid #727169;
    }
    QPushButton:pressed {
        background-color: #54546D;
    }
    QSlider::groove:horizontal {
        height: 6px;
        background: #54546D;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        width: 14px;
        height: 14px;
        background: #DCD7BA;
        border-radius: 7px;
    }
"""


class ColorWheelDialog(QDialog):
    """Popup dialog with an HSL colour disc."""

    color_selected = Signal(QColor)

    def __init__(self, initial_color: QColor, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pick a colour")
        self.setFixedSize(280, 400)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._disc = _ColorDisc(self)
        self._disc.set_color(initial_color)
        layout.addWidget(self._disc, alignment=Qt.AlignmentFlag.AlignCenter)

        # Saturation slider
        from PySide6.QtWidgets import QSlider
        sat_layout = QHBoxLayout()
        sat_label = QLabel("S:")
        sat_label.setStyleSheet("color: #DCD7BA; font-weight: bold;")
        sat_layout.addWidget(sat_label)
        self._sat_slider = QSlider(Qt.Orientation.Horizontal)
        self._sat_slider.setRange(0, 100)
        self._sat_slider.setValue(int(initial_color.getHslF()[1] * 100))
        self._sat_slider.setFixedHeight(20)
        self._sat_slider.valueChanged.connect(self._on_sat_changed)
        sat_layout.addWidget(self._sat_slider)
        self._sat_value = QLabel(f"{self._sat_slider.value()}%")
        self._sat_value.setStyleSheet("color: #DCD7BA; min-width: 32px;")
        sat_layout.addWidget(self._sat_value)
        layout.addLayout(sat_layout)

        # Preview + buttons row
        row = QHBoxLayout()

        self._preview = QLabel()
        self._preview.setFixedSize(32, 32)
        self._preview.setStyleSheet(f"""
            QLabel {{
                background-color: {initial_color.name()};
                border: 2px solid #727169;
                border-radius: 16px;
            }}
        """)
        row.addWidget(self._preview)

        row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(32)
        ok_btn.clicked.connect(self.accept)
        row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(32)
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(cancel_btn)

        layout.addLayout(row)

        self._disc.color_changed.connect(self._on_color_changed)

    def _on_sat_changed(self, value: int) -> None:
        self._disc.set_saturation(value / 100.0)
        self._sat_value.setText(f"{value}%")

    def _on_color_changed(self, color: QColor) -> None:
        self._preview.setStyleSheet(f"""
            QLabel {{
                background-color: {color.name()};
                border: 2px solid #727169;
                border-radius: 16px;
            }}
        """)

    def selected_color(self) -> QColor:
        return self._disc.color()
