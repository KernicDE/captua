"""Floating pill toolbars: four corner clusters (close, actions, tools, properties)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSlider,
    QWidget,
)

from .icons import icon
from .popups import EmojiPopup, MagnifierPopup, ShapePopup
from .theme import (
    ACTION_BUTTON_STYLE,
    EDIT_STYLE,
    MENU_STYLE,
    PILL_STYLE,
    PRIMARY_BUTTON_STYLE,
    SEPARATOR_STYLE,
    SLIDER_STYLE,
    TEXT,
    TOOL_BUTTON_STYLE,
)

_PILL_HEIGHT = 40


def _make_pill(parent: QWidget) -> tuple[QWidget, QHBoxLayout]:
    """Single floating pill container with a horizontal layout."""
    pill = QWidget(parent)
    pill.setObjectName("toolbarPill")
    # Plain QWidgets only paint stylesheet backgrounds with this set
    pill.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    pill.setStyleSheet(PILL_STYLE)
    pill.setFixedHeight(_PILL_HEIGHT)
    layout = QHBoxLayout(pill)
    layout.setContentsMargins(8, 4, 8, 4)
    layout.setSpacing(4)
    return pill, layout


def _make_separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFixedWidth(1)
    sep.setStyleSheet(SEPARATOR_STYLE)
    return sep


class ToolButton(QPushButton):
    """Single tool button with active state styling and a crisp icon."""

    def __init__(self, icon_name: str, name: str, shortcut: str = "", parent=None) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self.setStyleSheet(TOOL_BUTTON_STYLE)
        tooltip = f"{name} ({shortcut})" if shortcut else name
        self.setToolTip(tooltip)
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
                border: 2px solid #5A5A5A;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                border: 2px solid {TEXT};
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
    """Owns the four floating pill toolbars and all tool/property logic.

    The pills are direct children of the overlay window and are positioned
    by it (corners). This widget itself is a hidden logic container:

    - pill_close  (top-left):     close button
    - pill_actions(top-right):    Backdrop, Snap, Import, Capture | Save, Copy
    - pill_tools  (bottom-left):  the 17 tool buttons + sticky pin
    - pill_props  (bottom-right): contextual stroke/fill controls
    """

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
    snap_toggled = Signal(bool)
    sticky_toggled = Signal(bool)
    pills_changed = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        # The container itself never shows; only the pills do.
        self.hide()

        # ---- top-left: close --------------------------------------------------
        self.pill_close, close_layout = _make_pill(parent)
        self._close_btn = ToolButton("close", "Close", "Esc")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.clicked.connect(self.close_triggered.emit)
        close_layout.addWidget(self._close_btn)

        # ---- top-right: actions -------------------------------------------------
        self.pill_actions, action_layout = _make_pill(parent)

        self._backdrop_btn = QPushButton("Backdrop")
        self._backdrop_btn.setFixedHeight(28)
        self._backdrop_btn.setStyleSheet(ACTION_BUTTON_STYLE)
        self._backdrop_btn.setToolTip("Backdrop settings")
        self._backdrop_btn.clicked.connect(self.backdrop_settings_triggered.emit)
        action_layout.addWidget(self._backdrop_btn)

        self._snap_btn = QPushButton("Snap")
        self._snap_btn.setCheckable(True)
        self._snap_btn.setChecked(True)
        self._snap_btn.setFixedHeight(28)
        self._snap_btn.setStyleSheet(ACTION_BUTTON_STYLE)
        self._snap_btn.setToolTip("Toggle magnetic snap")
        self._snap_btn.clicked.connect(lambda checked: self.snap_toggled.emit(checked))
        action_layout.addWidget(self._snap_btn)

        self._import_btn = self._make_icon_action("import", "Import image…")
        self._import_btn.clicked.connect(self.import_image_triggered.emit)
        action_layout.addWidget(self._import_btn)

        self._capture_btn = self._make_icon_action("capture", "Capture region")
        self._capture_btn.clicked.connect(self.capture_triggered.emit)
        action_layout.addWidget(self._capture_btn)

        action_layout.addWidget(_make_separator())

        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedHeight(28)
        self._save_btn.setStyleSheet(ACTION_BUTTON_STYLE)
        self._save_btn.setToolTip("Save (Ctrl+S)")
        self._save_btn.clicked.connect(self.save_triggered.emit)
        action_layout.addWidget(self._save_btn)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedHeight(28)
        self._copy_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self._copy_btn.setToolTip("Copy & save (Ctrl+C)")
        self._copy_btn.clicked.connect(self.copy_triggered.emit)
        action_layout.addWidget(self._copy_btn)

        # ---- bottom-left: tools --------------------------------------------------
        self.pill_tools, tools_layout = _make_pill(parent)

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
            ("eyedropper", "D", "eyedropper", "Picker"),
        ]

        for key, sc, icon_name, name in tools:
            btn = ToolButton(icon_name, name, sc)
            btn.clicked.connect(lambda checked, k=key: self._on_tool_clicked(k))
            self._buttons[key] = btn
            tools_layout.addWidget(btn)

        self._buttons["select"].setChecked(True)

        # Sticky-tools toggle: keep the active tool after drawing
        self._sticky_btn = ToolButton("pin", "Keep tool active after drawing")
        self._sticky_btn.setFixedSize(28, 32)
        self._sticky_btn.setChecked(False)
        self._sticky_btn.clicked.connect(lambda checked: self.sticky_toggled.emit(checked))
        tools_layout.addWidget(self._sticky_btn)

        # ---- bottom-right: contextual properties ---------------------------------
        self.pill_props, props_layout = _make_pill(parent)

        stroke_icon = QLabel()
        stroke_icon.setPixmap(icon("stroke"))
        stroke_icon.setToolTip("Stroke colour and width")
        props_layout.addWidget(stroke_icon)

        self._line_color_btn = ColorSwatch()
        self._line_color_btn.color_changed.connect(self.line_color_changed.emit)
        props_layout.addWidget(self._line_color_btn)

        self._line_width_slider = QSlider(Qt.Orientation.Horizontal)
        self._line_width_slider.setRange(1, 20)
        self._line_width_slider.setValue(3)
        self._line_width_slider.setFixedWidth(48)
        self._line_width_slider.setStyleSheet(SLIDER_STYLE)
        self._line_width_slider.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._line_width_slider.valueChanged.connect(self._on_line_width_changed)
        props_layout.addWidget(self._line_width_slider)

        self._line_width_edit = QLineEdit("3")
        self._line_width_edit.setFixedWidth(28)
        self._line_width_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._line_width_edit.setStyleSheet(EDIT_STYLE)
        self._line_width_edit.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._line_width_edit.editingFinished.connect(self._on_line_width_edit_changed)
        props_layout.addWidget(self._line_width_edit)
        self._on_line_width_changed(3)

        props_layout.addSpacing(6)

        fill_icon = QLabel()
        fill_icon.setPixmap(icon("fill"))
        fill_icon.setToolTip("Fill colour and opacity")
        props_layout.addWidget(fill_icon)

        self._fill_color_btn = ColorSwatch()
        self._fill_color_btn.color_changed.connect(self.fill_color_changed.emit)
        props_layout.addWidget(self._fill_color_btn)

        self._fill_alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self._fill_alpha_slider.setRange(0, 100)
        self._fill_alpha_slider.setValue(50)
        self._fill_alpha_slider.setFixedWidth(48)
        self._fill_alpha_slider.setStyleSheet(SLIDER_STYLE)
        self._fill_alpha_slider.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._fill_alpha_slider.valueChanged.connect(self._on_fill_alpha_changed)
        props_layout.addWidget(self._fill_alpha_slider)

        self._fill_alpha_edit = QLineEdit("50%")
        self._fill_alpha_edit.setFixedWidth(32)
        self._fill_alpha_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fill_alpha_edit.setStyleSheet(EDIT_STYLE)
        self._fill_alpha_edit.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self._fill_alpha_edit.editingFinished.connect(self._on_fill_alpha_edit_changed)
        props_layout.addWidget(self._fill_alpha_edit)
        self._on_fill_alpha_changed(50)

        # Freeze each pill at its natural width
        self._pills = [self.pill_close, self.pill_actions, self.pill_tools, self.pill_props]
        self._props_visible = True  # until the first set_properties_visible call
        for pill in self._pills:
            pill.layout().activate()
            pill.setFixedWidth(pill.sizeHint().width())
            pill.hide()

        self._full_width = self._compute_full_width()

        # Popups (lazy)
        self._shape_popup: ShapePopup | None = None
        self._emoji_popup: EmojiPopup | None = None
        self._mag_zoom_popup: MagnifierPopup | None = None
        self._current_mag_zoom: float = 2.0

    @staticmethod
    def _make_icon_action(icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        pm = icon(icon_name)
        btn.setIcon(pm)
        btn.setIconSize(pm.size())
        btn.setFixedSize(28, 28)
        btn.setStyleSheet(ACTION_BUTTON_STYLE)
        btn.setToolTip(tooltip)
        return btn

    def _compute_full_width(self) -> int:
        """Window width needed so both pill rows fit side by side (+margins)."""
        top = self.pill_close.width() + self.pill_actions.width()
        bottom = self.pill_tools.width() + self.pill_props.width()
        return max(top, bottom) + 40  # outer margins + gap between pills

    # -- pill visibility / sizing (called from overlay) -------------------------

    def set_pills_visible(self, visible: bool) -> None:
        for pill in self._pills:
            pill.setVisible(visible)
        if visible and not self._props_visible:
            self.pill_props.hide()
        self.pills_changed.emit()

    def full_width(self) -> int:
        """Minimum window width so all four pills fit (see _compute_full_width)."""
        return self._full_width

    def refresh_full_width(self) -> None:
        """Recompute pill widths once the window is shown (font metrics are
        unreliable before the first show)."""
        for pill in self._pills:
            pill.setFixedWidth(pill.sizeHint().width())
        self._full_width = self._compute_full_width()
        self.pills_changed.emit()

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

    def set_copy_enabled(self, enabled: bool) -> None:
        self._copy_btn.setEnabled(enabled)

    def set_sticky(self, enabled: bool) -> None:
        self._sticky_btn.setChecked(enabled)
        self._sticky_btn._update_icon()

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
        self._props_visible = visible
        self.pill_props.setVisible(visible and self.pill_tools.isVisible())
        self.pills_changed.emit()

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
            Qt.Key.Key_D: "eyedropper",
            Qt.Key.Key_S: "shape",
            Qt.Key.Key_E: "emoji",
        }
        if event.key() in mapping:
            self.set_tool(mapping[event.key()])
            event.accept()
            return
        super().keyPressEvent(event)
