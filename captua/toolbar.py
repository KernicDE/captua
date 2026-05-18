"""Toolbar and properties bar."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .icons import icon
from .popups import EmojiPopup, MagnifierPopup, ShapePopup

_TOOL_BTN_STYLE = """
    QPushButton {
        background-color: #27272A;
        color: #A1A1AA;
        border: 1px solid #3F3F46;
        border-radius: 8px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #3F3F46;
        border: 1px solid #52525B;
        color: #F4F4F5;
    }
    QPushButton:pressed {
        background-color: #52525B;
    }
"""

_ACTION_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #A1A1AA;
        border: none;
        border-radius: 6px;
        font-size: 13px;
        padding: 2px 8px;
    }
    QPushButton:hover {
        background-color: #3F3F46;
        color: #F4F4F5;
    }
    QPushButton:pressed {
        background-color: #52525B;
    }
"""

_EDIT_STYLE = """
    QLineEdit {
        background-color: #27272A;
        color: #F4F4F5;
        border: 1px solid #3F3F46;
        border-radius: 4px;
        padding: 0 2px;
        font-size: 12px;
    }
    QLineEdit:focus {
        border: 1px solid #7E9CD8;
    }
"""


def _make_separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFixedWidth(1)
    sep.setStyleSheet("QFrame { background-color: #3F3F46; border: none; }")
    return sep


class ToolButton(QPushButton):
    """Single tool button with active state styling and a crisp icon."""

    def __init__(self, icon_name: str, name: str, shortcut: str, parent=None) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self.setStyleSheet(_TOOL_BTN_STYLE + """
            QPushButton:checked {
                background-color: #2D4F67;
                border: 1px solid #7E9CD8;
                color: #F4F4F5;
            }
        """)
        self.setToolTip(f"{name} ({shortcut})")
        self._update_icon()

    def _update_icon(self) -> None:
        pm = icon(self._icon_name, active=self.isChecked())
        self.setIcon(pm)
        self.setIconSize(pm.size())

    def nextCheckState(self) -> None:
        super().nextCheckState()
        self._update_icon()


class ColorSwatch(QPushButton):
    """Color picker button — opens a colour-wheel dialog on click."""

    color_changed = Signal(QColor)

    def __init__(self, initial_color: QColor | None = None, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(initial_color) if initial_color is not None else QColor("#FF5D62")
        self.setFixedSize(24, 24)
        self._update_style()
        self.setToolTip("Click to pick a colour")
        self.clicked.connect(self._open_wheel)

    def _update_style(self) -> None:
        c = self._color.name()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {c};
                border: 2px solid #71717A;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                border: 2px solid #F4F4F5;
            }}
        """)

    def _open_wheel(self) -> None:
        from .colorwheel import ColorWheelDialog
        dialog = ColorWheelDialog(self._color, self)
        if dialog.exec() == 1:  # Accepted
            self._color = dialog.selected_color()
            self._update_style()
            self.color_changed.emit(self._color)

    def color(self) -> QColor:
        return self._color

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self._update_style()


class Toolbar(QWidget):
    """Top toolbar with action buttons, tool buttons and property controls."""

    tool_changed = Signal(str)
    line_color_changed = Signal(QColor)
    line_width_changed = Signal(float)
    fill_color_changed = Signal(QColor)
    fill_alpha_changed = Signal(int)
    shape_selected = Signal(str)
    emoji_selected = Signal(str)
    close_triggered = Signal()
    save_triggered = Signal()
    copy_triggered = Signal()
    import_image_triggered = Signal()
    capture_triggered = Signal()
    backdrop_settings_triggered = Signal()
    magnifier_zoom_changed = Signal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(76)
        self.setStyleSheet("background-color: #18181B;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 4)
        main_layout.setSpacing(4)

        # ---- top row: action buttons ------------------------------------------
        action_row = QHBoxLayout()
        action_row.setSpacing(4)

        has_frameless = False
        if parent is not None:
            has_frameless = bool(parent.windowFlags() & Qt.WindowType.FramelessWindowHint)

        if has_frameless:
            self._close_btn = QPushButton("✕")
            self._close_btn.setFixedSize(32, 28)
            self._close_btn.setStyleSheet(_ACTION_BTN_STYLE)
            self._close_btn.setToolTip("Close (Esc)")
            action_row.addWidget(self._close_btn)
            self._close_btn.clicked.connect(self.close_triggered.emit)
        else:
            self._close_btn = None

        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedSize(48, 28)
        self._save_btn.setStyleSheet(_ACTION_BTN_STYLE)
        self._save_btn.setToolTip("Save (Ctrl+S)")
        action_row.addWidget(self._save_btn)
        self._save_btn.clicked.connect(self.save_triggered.emit)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedSize(48, 28)
        self._copy_btn.setStyleSheet(_ACTION_BTN_STYLE)
        self._copy_btn.setToolTip("Copy & save (Ctrl+C)")
        action_row.addWidget(self._copy_btn)
        self._copy_btn.clicked.connect(self.copy_triggered.emit)

        self._import_btn = QPushButton("Import")
        self._import_btn.setFixedSize(52, 28)
        self._import_btn.setStyleSheet(_ACTION_BTN_STYLE)
        self._import_btn.setToolTip("Import image")
        action_row.addWidget(self._import_btn)
        self._import_btn.clicked.connect(self.import_image_triggered.emit)

        self._capture_btn = QPushButton("Capture")
        self._capture_btn.setFixedSize(56, 28)
        self._capture_btn.setStyleSheet(_ACTION_BTN_STYLE)
        self._capture_btn.setToolTip("Capture region")
        action_row.addWidget(self._capture_btn)
        self._capture_btn.clicked.connect(self.capture_triggered.emit)

        action_row.addWidget(_make_separator())

        # Backdrop button (non-tool, shows popup)
        self._backdrop_btn = QPushButton("Backdrop")
        self._backdrop_btn.setFixedSize(64, 28)
        self._backdrop_btn.setStyleSheet(_ACTION_BTN_STYLE)
        self._backdrop_btn.setToolTip("Backdrop settings")
        self._backdrop_btn.clicked.connect(self.backdrop_settings_triggered.emit)
        action_row.addWidget(self._backdrop_btn)

        action_row.addStretch()
        main_layout.addLayout(action_row)

        # ---- bottom row: tools + properties -----------------------------------
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(4)

        # Tool buttons
        self._buttons: dict[str, ToolButton] = {}
        self._active = "select"

        tools = [
            ("select",    "V", "select",  "Mouse"),
            ("rectangle", "R", "rectangle",  "Rectangle"),
            ("ellipse",   "O", "ellipse",  "Ellipse"),
            ("line",      "L", "line",  "Line"),
            ("arrow",     "A", "arrow",  "Arrow"),
            ("pen",       "P", "pen",  "Pen"),
            ("marker",    "M", "marker",  "Marker"),
            ("shape",     "S", "shape",  "Forms"),
            ("emoji",     "E", "emoji", "Emojis"),
            ("text",      "T", "text",   "Text"),
            ("label",     "K", "label",  "Label"),
            ("counter",   "N", "counter",  "Numbering"),
            ("ruler",     "U", "ruler",  "Ruler"),
            ("spotlight", "I", "spotlight",  "Highlight"),
            ("blur",      "B", "blur",  "Blur"),
            ("magnifier", "G", "magnifier",  "Magnifier"),
        ]

        for key, sc, icon_name, name in tools:
            btn = ToolButton(icon_name, name, sc)
            btn.clicked.connect(lambda checked, k=key: self._on_tool_clicked(k))
            self._buttons[key] = btn
            bottom_row.addWidget(btn)

        self._buttons["select"].setChecked(True)

        bottom_row.addWidget(_make_separator())

        # Properties panel (contextual)
        self._props_widget = QWidget(self)
        self._props_widget.setStyleSheet("background: transparent;")
        props_layout = QHBoxLayout(self._props_widget)
        props_layout.setContentsMargins(0, 0, 0, 0)
        props_layout.setSpacing(4)

        # Line color + width
        self._line_color_btn = ColorSwatch()
        self._line_color_btn.color_changed.connect(self.line_color_changed.emit)
        props_layout.addWidget(self._line_color_btn)

        props_layout.addSpacing(4)

        self._line_width_slider = QSlider(Qt.Orientation.Horizontal)
        self._line_width_slider.setRange(1, 20)
        self._line_width_slider.setValue(3)
        self._line_width_slider.setFixedWidth(50)
        self._line_width_slider.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._line_width_slider.valueChanged.connect(self._on_line_width_changed)
        props_layout.addWidget(self._line_width_slider)

        self._line_width_edit = QLineEdit("3")
        self._line_width_edit.setFixedWidth(32)
        self._line_width_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._line_width_edit.setStyleSheet(_EDIT_STYLE)
        self._line_width_edit.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._line_width_edit.editingFinished.connect(self._on_line_width_edit_changed)
        props_layout.addWidget(self._line_width_edit)
        self._on_line_width_changed(3)

        props_layout.addSpacing(8)

        # Fill color + alpha
        self._fill_color_btn = ColorSwatch()
        self._fill_color_btn.color_changed.connect(self.fill_color_changed.emit)
        props_layout.addWidget(self._fill_color_btn)

        props_layout.addSpacing(4)

        self._fill_alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self._fill_alpha_slider.setRange(0, 100)
        self._fill_alpha_slider.setValue(50)
        self._fill_alpha_slider.setFixedWidth(50)
        self._fill_alpha_slider.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._fill_alpha_slider.valueChanged.connect(self._on_fill_alpha_changed)
        props_layout.addWidget(self._fill_alpha_slider)

        self._fill_alpha_edit = QLineEdit("50%")
        self._fill_alpha_edit.setFixedWidth(40)
        self._fill_alpha_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fill_alpha_edit.setStyleSheet(_EDIT_STYLE)
        self._fill_alpha_edit.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._fill_alpha_edit.editingFinished.connect(self._on_fill_alpha_edit_changed)
        props_layout.addWidget(self._fill_alpha_edit)
        self._on_fill_alpha_changed(50)

        bottom_row.addWidget(self._props_widget)
        bottom_row.addStretch()
        main_layout.addLayout(bottom_row)

        # Popups (lazy)
        self._shape_popup: ShapePopup | None = None
        self._emoji_popup: EmojiPopup | None = None
        self._mag_zoom_popup: MagnifierPopup | None = None
        self._current_mag_zoom: float = 2.0

        # Enforce minimum width so the window can't be narrowed below content
        self.layout().activate()
        self.setMinimumWidth(self.minimumSizeHint().width())

    # -- tool routing ---------------------------------------------------------

    def _on_tool_clicked(self, key: str) -> None:
        reclick = self._active == key
        if not reclick:
            self._active = key
            for k, btn in self._buttons.items():
                btn.setChecked(k == key)
                btn._update_icon()
            self.tool_changed.emit(key)

        if key == "shape":
            self._show_shape_popup()
        elif key == "emoji":
            self._show_emoji_popup()
        elif key == "magnifier":
            self._show_magnifier_popup()

    def _show_shape_popup(self) -> None:
        btn = self._buttons.get("shape")
        if btn is None:
            return
        if self._shape_popup is None:
            self._shape_popup = ShapePopup()
            self._shape_popup.shape_selected.connect(self.shape_selected.emit)
        self._shape_popup.show_below(btn)

    def _show_emoji_popup(self) -> None:
        btn = self._buttons.get("emoji")
        if btn is None:
            return
        if self._emoji_popup is None:
            self._emoji_popup = EmojiPopup()
            self._emoji_popup.emoji_selected.connect(self.emoji_selected.emit)
        self._emoji_popup.show_below(btn)

    def _show_magnifier_popup(self) -> None:
        btn = self._buttons.get("magnifier")
        if btn is None:
            return
        if self._mag_zoom_popup is None:
            self._mag_zoom_popup = MagnifierPopup(self._current_mag_zoom)
            self._mag_zoom_popup.zoom_changed.connect(self.magnifier_zoom_changed.emit)
        else:
            self._mag_zoom_popup.set_zoom(self._current_mag_zoom)
        self._mag_zoom_popup.show_below(btn)

    # -- property setters (called from overlay) --------------------------------

    def set_line_color(self, color: QColor) -> None:
        self._line_color_btn.set_color(color)

    def set_line_width(self, width: float) -> None:
        self._line_width_slider.blockSignals(True)
        self._line_width_slider.setValue(int(width))
        self._line_width_slider.blockSignals(False)
        self._on_line_width_changed(int(width))

    def set_fill_color(self, color: QColor) -> None:
        self._fill_color_btn.set_color(color)

    def set_fill_alpha(self, alpha: int) -> None:
        self._fill_alpha_slider.blockSignals(True)
        self._fill_alpha_slider.setValue(int(alpha / 255 * 100))
        self._fill_alpha_slider.blockSignals(False)
        self._on_fill_alpha_changed(int(alpha / 255 * 100))

    def set_magnifier_zoom(self, zoom: float) -> None:
        self._current_mag_zoom = zoom
        if self._mag_zoom_popup is not None and self._mag_zoom_popup.isVisible():
            self._mag_zoom_popup.set_zoom(zoom)

    def set_tool(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].click()

    def backdrop_button(self) -> QPushButton:
        return self._backdrop_btn

    def update_active_tool_button(self, key: str) -> None:
        """Sync button visual state without emitting tool_changed."""
        if key not in self._buttons:
            return
        self._active = key
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)
            btn._update_icon()

    def active_tool(self) -> str:
        return self._active

    def set_properties_visible(self, visible: bool) -> None:
        self._props_widget.setVisible(visible)

    # -- change handlers -------------------------------------------------------

    def _on_line_width_changed(self, value: int) -> None:
        self._line_width_slider.setToolTip(f"{value} px")
        self._line_width_edit.setText(str(value))
        self.line_width_changed.emit(float(value))

    def _on_line_width_edit_changed(self) -> None:
        try:
            value = int(self._line_width_edit.text())
            value = max(1, min(20, value))
        except ValueError:
            value = self._line_width_slider.value()
        self._line_width_slider.setValue(value)

    def _on_fill_alpha_changed(self, value: int) -> None:
        self._fill_alpha_slider.setToolTip(f"{value}%")
        self._fill_alpha_edit.setText(f"{value}%")
        self.fill_alpha_changed.emit(int(value / 100 * 255))

    def _on_fill_alpha_edit_changed(self) -> None:
        try:
            text = self._fill_alpha_edit.text().replace("%", "")
            value = int(text)
            value = max(0, min(100, value))
        except ValueError:
            value = self._fill_alpha_slider.value()
        self._fill_alpha_slider.setValue(value)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        mapping = {
            Qt.Key.Key_V: "select",
            Qt.Key.Key_R: "rectangle",
            Qt.Key.Key_O: "ellipse",
            Qt.Key.Key_L: "line",
            Qt.Key.Key_A: "arrow",
            Qt.Key.Key_P: "pen",
            Qt.Key.Key_M: "marker",
            Qt.Key.Key_T: "text",
            Qt.Key.Key_K: "label",
            Qt.Key.Key_N: "counter",
            Qt.Key.Key_U: "ruler",
            Qt.Key.Key_I: "spotlight",
            Qt.Key.Key_B: "blur",
            Qt.Key.Key_G: "magnifier",
            Qt.Key.Key_S: "shape",
            Qt.Key.Key_E: "emoji",
        }
        if event.key() in mapping:
            self.set_tool(mapping[event.key()])
            event.accept()
        else:
            super().keyPressEvent(event)
