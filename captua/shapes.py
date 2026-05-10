"""Shape picker dialog for selecting geometric shapes."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

_SHAPES = [
    ("heart", "♥", "Heart"),
    ("star5", "★", "Star"),
    ("star4", "✦", "4-Point Star"),
    ("triangle", "▲", "Triangle"),
    ("diamond", "◆", "Diamond"),
    ("hexagon", "⬡", "Hexagon"),
    ("arrow_shape", "➤", "Arrow"),
    ("cross", "✚", "Cross"),
    ("moon", "☾", "Moon"),
]

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
"""

_BTN_STYLE = _DIALOG_STYLE + """
    QPushButton {
        font-size: 22px;
        min-width: 64px;
        min-height: 48px;
    }
    QPushButton:checked {
        background-color: #2D4F67;
        border: 1px solid #7E9CD8;
    }
"""


class ShapePickerDialog(QDialog):
    """Grid dialog for picking a geometric shape."""

    shape_selected = Signal(str)

    def __init__(self, current_shape: str = "heart", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Shape")
        self.setFixedSize(340, 280)
        self.setStyleSheet(_DIALOG_STYLE)
        self._selected = current_shape

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(8)

        self._buttons: dict[str, QPushButton] = {}
        for i, (key, icon, tooltip) in enumerate(_SHAPES):
            btn = QPushButton(icon)
            btn.setFixedSize(80, 56)
            btn.setStyleSheet(_BTN_STYLE)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setChecked(key == current_shape)
            btn.clicked.connect(lambda checked, k=key: self._on_shape_clicked(k))
            self._buttons[key] = btn
            grid.addWidget(btn, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_shape_clicked(self, key: str) -> None:
        self._selected = key
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)

    def selected_shape(self) -> str:
        return self._selected
