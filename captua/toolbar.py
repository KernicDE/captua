"""Floating pill toolbars: four corner clusters (close, actions, tools, properties)."""

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QWidget,
)

from .icons import icon
from .popups import PRESET_COLORS, ColorPalettePopup, EmojiPopup, ShapePopup
from .theme import (
    ACTION_BUTTON_STYLE,
    EDIT_STYLE,
    MENU_STYLE,
    PILL_STYLE,
    PRIMARY_BUTTON_STYLE,
    SEPARATOR_STYLE,
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
        self.setAccessibleName(name)
        self._update_icon()

    def _update_icon(self) -> None:
        pm = icon(self._icon_name, active=self.isChecked())
        self.setIcon(pm)
        self.setIconSize(pm.size())

    def nextCheckState(self) -> None:
        super().nextCheckState()
        self._update_icon()


class ColorSwatch(QPushButton):
    """Colour button: hovering shows a row of fixed colours above it."""

    color_changed = Signal(QColor)

    def __init__(self, initial_color: QColor | None = None, parent=None, colors: list[tuple[str, str]] = PRESET_COLORS) -> None:
        super().__init__(parent)
        self._color = QColor(initial_color) if initial_color is not None else QColor("#FF5D62")
        self._colors = colors
        self._palette: ColorPalettePopup | None = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(250)
        self._hide_timer.timeout.connect(self._hide_palette)
        self.setFixedSize(28, 28)
        self._update_style()
        self.setAccessibleName("Colour")
        self._update_tooltip()
        self.clicked.connect(self._show_palette)

    def _update_tooltip(self) -> None:
        self.setToolTip(f"Colour {self._color.name().upper()} - hover to change")

    def _update_style(self) -> None:
        self._update_tooltip()
        c = self._color.name()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {c};
                border: 2px solid #8A8A92;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                border: 2px solid {TEXT};
            }}
        """)

    # -- preset palette ------------------------------------------------------

    def _show_palette(self) -> None:
        win = self.window()
        if self._palette is None:
            self._palette = ColorPalettePopup(win, self._colors)
            self._palette.color_picked.connect(self._on_preset)
            self._palette.hover_changed.connect(self._on_palette_hover)
        pal = self._palette
        x = self.mapTo(win, QPoint(0, 0)).x() + (self.width() - pal.width()) // 2
        x = max(4, min(x, win.width() - pal.width() - 4))
        pal.move(x, self.mapTo(win, QPoint(0, 0)).y() - pal.height() - 4)
        pal.show()
        pal.raise_()

    def _hide_palette(self) -> None:
        if self._palette is not None:
            self._palette.hide()

    def _on_palette_hover(self, inside: bool) -> None:
        self._hide_timer.stop() if inside else self._hide_timer.start()

    def _on_preset(self, color: QColor) -> None:
        self.set_color(color)
        self.color_changed.emit(self._color)
        self._hide_palette()

    def enterEvent(self, event) -> None:
        self._hide_timer.stop()
        self._show_palette()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hide_timer.start()
        super().leaveEvent(event)

    def color(self) -> QColor:
        return self._color

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self._update_style()


_STEPPER_BTN_STYLE = ACTION_BUTTON_STYLE + "QPushButton { padding: 0; font-size: 15px; }"

_WIDTH_STEPS = [*range(1, 26), *range(30, 101, 5), *range(110, 201, 10)]
_ALPHA_STEPS = list(range(0, 101, 5))
_ZOOM_STEPS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


class Stepper(QWidget):
    """[-] value [+] control over a fixed list of steps (typed values snap to the nearest)."""

    value_changed = Signal(float)

    def __init__(self, steps: list[float], fmt, tooltip: str, edit_width: int = 34, parent=None) -> None:
        super().__init__(parent)
        self._steps = steps
        self._fmt = fmt
        self._i = 0
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        self._minus = self._make_btn("−", "Decrease", -1)
        self._plus = self._make_btn("+", "Increase", 1)
        self._edit = QLineEdit()
        self._edit.setFixedWidth(edit_width)
        self._edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._edit.setStyleSheet(EDIT_STYLE)
        self._edit.setToolTip(tooltip)
        self._edit.setAccessibleName(tooltip)
        self._edit.editingFinished.connect(self._on_edit)
        for w in (self._minus, self._edit, self._plus):
            row.addWidget(w)
        self.set_value(steps[0])

    def _make_btn(self, text: str, name: str, delta: int) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(22, 24)
        btn.setAutoRepeat(True)
        btn.setStyleSheet(_STEPPER_BTN_STYLE)
        btn.setAccessibleName(name)
        btn.clicked.connect(lambda: self._move(delta))
        return btn

    def value(self) -> float:
        return self._steps[self._i]

    def set_value(self, v: float) -> None:
        """Show the step nearest to `v` without emitting."""
        self._i = min(range(len(self._steps)), key=lambda i: abs(self._steps[i] - v))
        self._edit.setText(self._fmt(self._steps[self._i]))
        self._minus.setEnabled(self._i > 0)
        self._plus.setEnabled(self._i < len(self._steps) - 1)

    def _move(self, delta: int) -> None:
        i = max(0, min(len(self._steps) - 1, self._i + delta))
        if i != self._i:
            self.set_value(self._steps[i])
            self.value_changed.emit(self.value())

    def _on_edit(self) -> None:
        try:
            v = float(self._edit.text().replace("%", "").replace("x", "").replace("px", "").strip())
        except ValueError:
            v = self.value()
        old = self.value()
        self.set_value(v)
        if self.value() != old:
            self.value_changed.emit(self.value())


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

        self._line_width = Stepper(_WIDTH_STEPS, lambda v: f"{v:g}", "Stroke width (px)")
        self._line_width.set_value(3)
        self._line_width.value_changed.connect(self.line_width_changed.emit)
        props_layout.addWidget(self._line_width)

        props_layout.addSpacing(6)

        fill_icon = QLabel()
        fill_icon.setPixmap(icon("fill"))
        fill_icon.setToolTip("Fill colour and opacity")
        props_layout.addWidget(fill_icon)

        self._fill_color_btn = ColorSwatch()
        self._fill_color_btn.color_changed.connect(self.fill_color_changed.emit)
        props_layout.addWidget(self._fill_color_btn)

        self._fill_alpha = Stepper(_ALPHA_STEPS, lambda v: f"{v:g}%", "Fill opacity", edit_width=40)
        self._fill_alpha.set_value(50)
        self._fill_alpha.value_changed.connect(lambda v: self.fill_alpha_changed.emit(int(v / 100 * 255)))
        props_layout.addWidget(self._fill_alpha)

        # Magnifier zoom factor; only shown while a magnifier is relevant
        self._zoom_group = QWidget()
        zoom_row = QHBoxLayout(self._zoom_group)
        zoom_row.setContentsMargins(0, 0, 0, 0)
        zoom_row.setSpacing(4)
        zoom_row.addSpacing(6)
        zoom_label = QLabel("Zoom")
        zoom_label.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        zoom_row.addWidget(zoom_label)
        self._zoom = Stepper(_ZOOM_STEPS, lambda v: f"{v:.1f}x", "Magnifier zoom factor", edit_width=40)
        self._zoom.set_value(2.0)
        self._zoom.value_changed.connect(self._on_zoom_changed)
        zoom_row.addWidget(self._zoom)
        props_layout.addWidget(self._zoom_group)
        self._zoom_group.hide()

        # Freeze each pill at its natural width
        self._pills = [self.pill_close, self.pill_actions, self.pill_tools, self.pill_props]
        for pill in self._pills:
            pill.layout().activate()
            pill.setFixedWidth(pill.sizeHint().width())
            pill.hide()

        self._zoom_width = self._zoom_group.sizeHint().width() + props_layout.spacing()
        self._full_width = self._compute_full_width()

        # Popups (lazy)
        self._shape_popup: ShapePopup | None = None
        self._emoji_popup: EmojiPopup | None = None

    @staticmethod
    def _make_icon_action(icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        pm = icon(icon_name)
        btn.setIcon(pm)
        btn.setIconSize(pm.size())
        btn.setFixedSize(28, 28)
        btn.setStyleSheet(ACTION_BUTTON_STYLE)
        btn.setToolTip(tooltip)
        btn.setAccessibleName(tooltip)
        return btn

    def _compute_full_width(self) -> int:
        """Window width needed so both pill rows fit side by side (+margins)."""
        top = self.pill_close.width() + self.pill_actions.width()
        # reserve room for the zoom group so showing it never overflows the window
        extra = 0 if self._zoom_group.isVisibleTo(self.pill_props) else self._zoom_width
        bottom = self.pill_tools.width() + self.pill_props.width() + extra
        return max(top, bottom) + 40  # outer margins + gap between pills

    # -- pill visibility / sizing (called from overlay) -------------------------

    def set_pills_visible(self, visible: bool) -> None:
        for pill in self._pills:
            pill.setVisible(visible)
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

    def _show_shape_popup(self) -> None:
        btn = self._buttons.get("shape")
        if btn is None:
            return
        if self._shape_popup is None:
            self._shape_popup = ShapePopup()
            self._shape_popup.shape_selected.connect(self.shape_selected.emit)
        self._shape_popup.show_above(btn)

    def _show_emoji_popup(self) -> None:
        btn = self._buttons.get("emoji")
        if btn is None:
            return
        if self._emoji_popup is None:
            self._emoji_popup = EmojiPopup()
            self._emoji_popup.emoji_selected.connect(self.emoji_selected.emit)
        self._emoji_popup.show_above(btn)

    # -- property setters (called from overlay) --------------------------------

    def set_line_color(self, color: QColor) -> None:
        self._line_color_btn.set_color(color)

    def set_line_width(self, width: float) -> None:
        self._line_width.set_value(width)

    def set_fill_color(self, color: QColor) -> None:
        self._fill_color_btn.set_color(color)

    def set_fill_alpha(self, alpha: int) -> None:
        self._fill_alpha.set_value(alpha / 255 * 100)

    def set_magnifier_zoom(self, zoom: float) -> None:
        self._zoom.set_value(zoom)

    def set_zoom_visible(self, visible: bool) -> None:
        """Show the magnifier zoom stepper (resizes the props pill)."""
        if self._zoom_group.isVisibleTo(self.pill_props) == visible:
            return
        self._zoom_group.setVisible(visible)
        self.pill_props.layout().activate()
        self.pill_props.setFixedWidth(self.pill_props.sizeHint().width())
        self._full_width = self._compute_full_width()
        self.pills_changed.emit()

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

    # -- change handlers -------------------------------------------------------

    def _on_zoom_changed(self, zoom: float) -> None:
        self.magnifier_zoom_changed.emit(zoom)

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
