"""HSL colour disc picker dialog with HEX and RGB inputs."""

import math

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class _ColorDisc(QWidget):
    color_changed = Signal(QColor)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._hue = 0.0
        self._saturation = 1.0
        self._lightness = 0.5
        self._inverted = True  # True: white centre → black rim (default)
        self._cached: QImage | None = None
        self.setFixedSize(220, 220)
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
        background-color: #18181B;
    }
    QPushButton {
        background-color: #27272A;
        color: #F4F4F5;
        border: 1px solid #3F3F46;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #3F3F46;
        border: 1px solid #52525B;
    }
    QPushButton:pressed {
        background-color: #52525B;
    }
    QSlider::groove:horizontal {
        height: 6px;
        background: #3F3F46;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        width: 14px;
        height: 14px;
        background: #F4F4F5;
        border-radius: 7px;
    }
"""

_EDIT_STYLE = """
    QLineEdit {
        background-color: #27272A;
        color: #F4F4F5;
        border: 1px solid #3F3F46;
        border-radius: 4px;
        padding: 0 4px;
        font-size: 12px;
    }
    QLineEdit:focus {
        border: 1px solid #7E9CD8;
    }
"""

_SPIN_STYLE = """
    QSpinBox {
        background-color: #27272A;
        color: #F4F4F5;
        border: 1px solid #3F3F46;
        border-radius: 4px;
        padding: 0 4px;
        font-size: 12px;
    }
    QSpinBox:focus {
        border: 1px solid #7E9CD8;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 0px;
        border: none;
    }
"""


class ColorWheelDialog(QDialog):
    """Popup dialog with an HSL colour disc, HEX input, and RGB inputs."""

    color_selected = Signal(QColor)

    def __init__(self, initial_color: QColor, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pick a colour")
        self.setFixedSize(360, 340)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Top row: disc on the left, RGB on the right
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self._disc = _ColorDisc(self)
        self._disc.set_color(initial_color)
        top_row.addWidget(self._disc, alignment=Qt.AlignmentFlag.AlignTop)

        rgb_layout = QVBoxLayout()
        rgb_layout.setSpacing(6)
        rgb_layout.setContentsMargins(0, 8, 0, 0)

        self._r_edit = self._make_spinbox(initial_color.red())
        self._g_edit = self._make_spinbox(initial_color.green())
        self._b_edit = self._make_spinbox(initial_color.blue())
        for label, edit in [("R", self._r_edit), ("G", self._g_edit), ("B", self._b_edit)]:
            row = QHBoxLayout()
            row.setSpacing(4)
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("color: #F4F4F5; font-weight: bold;")
            row.addWidget(lbl)
            row.addWidget(edit)
            rgb_layout.addLayout(row)

        rgb_layout.addStretch()
        top_row.addLayout(rgb_layout)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Saturation slider
        sat_layout = QHBoxLayout()
        sat_label = QLabel("S:")
        sat_label.setStyleSheet("color: #F4F4F5; font-weight: bold;")
        sat_layout.addWidget(sat_label)
        self._sat_slider = QSlider(Qt.Orientation.Horizontal)
        self._sat_slider.setRange(0, 100)
        self._sat_slider.setValue(int(initial_color.getHslF()[1] * 100))
        self._sat_slider.setFixedHeight(20)
        self._sat_slider.valueChanged.connect(self._on_sat_changed)
        sat_layout.addWidget(self._sat_slider)
        self._sat_value = QLabel(f"{self._sat_slider.value()}%")
        self._sat_value.setStyleSheet("color: #F4F4F5; min-width: 32px;")
        sat_layout.addWidget(self._sat_value)
        layout.addLayout(sat_layout)

        # Preview + HEX + buttons row
        row = QHBoxLayout()
        row.setSpacing(8)

        self._preview = QLabel()
        self._preview.setFixedSize(28, 28)
        self._update_preview(initial_color)
        row.addWidget(self._preview)

        hex_label = QLabel("HEX:")
        hex_label.setStyleSheet("color: #F4F4F5; font-weight: bold;")
        row.addWidget(hex_label)
        self._hex_edit = QLineEdit(initial_color.name().upper())
        self._hex_edit.setStyleSheet(_EDIT_STYLE)
        self._hex_edit.setFixedWidth(90)
        self._hex_edit.editingFinished.connect(self._on_hex_changed)
        row.addWidget(self._hex_edit)

        row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(28)
        ok_btn.clicked.connect(self.accept)
        row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(28)
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(cancel_btn)

        layout.addLayout(row)

        self._disc.color_changed.connect(self._on_disc_color_changed)
        for edit in (self._r_edit, self._g_edit, self._b_edit):
            edit.valueChanged.connect(self._on_rgba_changed)

    def _make_spinbox(self, value: int) -> QSpinBox:
        sb = QSpinBox()
        sb.setRange(0, 255)
        sb.setValue(value)
        sb.setFixedWidth(56)
        sb.setStyleSheet(_SPIN_STYLE)
        return sb

    def _on_sat_changed(self, value: int) -> None:
        self._sat_value.setText(f"{value}%")
        self._disc.set_saturation(value / 100.0)

    def _on_disc_color_changed(self, color: QColor) -> None:
        self._r_edit.blockSignals(True)
        self._g_edit.blockSignals(True)
        self._b_edit.blockSignals(True)
        self._r_edit.setValue(color.red())
        self._g_edit.setValue(color.green())
        self._b_edit.setValue(color.blue())
        self._r_edit.blockSignals(False)
        self._g_edit.blockSignals(False)
        self._b_edit.blockSignals(False)
        self._hex_edit.setText(color.name().upper())
        self._update_preview(color)

    def _on_rgba_changed(self) -> None:
        color = QColor(
            self._r_edit.value(),
            self._g_edit.value(),
            self._b_edit.value(),
        )
        self._disc.blockSignals(True)
        self._disc.set_color(color)
        self._disc.blockSignals(False)
        self._hex_edit.setText(color.name().upper())
        self._update_preview(color)

    def _on_hex_changed(self) -> None:
        text = self._hex_edit.text().strip()
        color = QColor(text)
        if color.isValid():
            self._disc.blockSignals(True)
            self._disc.set_color(color)
            self._disc.blockSignals(False)
            self._r_edit.blockSignals(True)
            self._g_edit.blockSignals(True)
            self._b_edit.blockSignals(True)
            self._r_edit.setValue(color.red())
            self._g_edit.setValue(color.green())
            self._b_edit.setValue(color.blue())
            self._r_edit.blockSignals(False)
            self._g_edit.blockSignals(False)
            self._b_edit.blockSignals(False)
            self._update_preview(color)

    def _update_preview(self, color: QColor) -> None:
        self._preview.setStyleSheet(f"""
            QLabel {{
                background-color: {color.name()};
                border: 2px solid #71717A;
                border-radius: 14px;
            }}
        """)

    def selected_color(self) -> QColor:
        return self._disc.color()
