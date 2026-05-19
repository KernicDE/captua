"""Backdrop settings — popup widget (no OK/Cancel, live changes)."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtCore import QEvent
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .toolbar import ColorSwatch

_POPUP_STYLE = """
    QFrame#backdrop_frame {
        background-color: #27272A;
        border: 1px solid #3F3F46;
        border-radius: 8px;
    }
    QLabel {
        color: #F4F4F5;
        font-size: 12px;
        background: transparent;
        border: none;
    }
    QCheckBox {
        color: #F4F4F5;
        font-size: 12px;
        background: transparent;
        border: none;
    }
    QCheckBox::indicator {
        width: 14px;
        height: 14px;
        border-radius: 3px;
        border: 1px solid #3F3F46;
        background: #18181B;
    }
    QCheckBox::indicator:checked {
        background: #7E9CD8;
        border-color: #7E9CD8;
    }
    QSlider::groove:horizontal {
        height: 4px;
        background: #3F3F46;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #7E9CD8;
        width: 14px;
        height: 14px;
        border-radius: 7px;
        margin: -5px 0;
    }
    QSlider::sub-page:horizontal {
        background: #7E9CD8;
        border-radius: 2px;
    }
"""


class BackdropPopup(QWidget):
    """Popup panel for backdrop settings — appears below toolbar button, live preview."""

    def __init__(self, scene, view, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._scene = scene
        self._view = view

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame(self)
        frame.setObjectName("backdrop_frame")
        frame.setStyleSheet(_POPUP_STYLE)
        outer.addWidget(frame)

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(14, 12, 14, 14)
        inner.setSpacing(8)

        # On/Off toggle
        self._enabled_check = QCheckBox("Show backdrop")
        self._enabled_check.setChecked(getattr(scene, "backdrop_enabled", True))
        self._enabled_check.stateChanged.connect(self._apply)
        inner.addWidget(self._enabled_check)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setSpacing(6)
        form.setContentsMargins(0, 0, 0, 0)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Colour / Gradient radio group
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        self._mode_group = QButtonGroup(self)
        self._mode_colour = QRadioButton("Colour")
        self._mode_gradient = QRadioButton("Gradient")
        self._mode_group.addButton(self._mode_colour)
        self._mode_group.addButton(self._mode_gradient)
        self._mode_colour.setChecked(not scene.backdrop_use_gradient)
        self._mode_gradient.setChecked(scene.backdrop_use_gradient)
        self._mode_colour.toggled.connect(self._apply)
        mode_row.addWidget(self._mode_colour)
        mode_row.addWidget(self._mode_gradient)
        mode_row.addStretch()
        form.addRow(mode_row)

        # Solid backdrop color (shown when Colour mode)
        self._color_btn = ColorSwatch(QColor(scene.backdrop_color))
        self._color_btn.color_changed.connect(self._apply)
        form.addRow(self._color_btn)

        # Gradient start / end (shown when Gradient mode)
        grad_row = QHBoxLayout()
        grad_row.setSpacing(6)
        self._grad_start_btn = ColorSwatch(QColor(scene.backdrop_gradient_start))
        self._grad_start_btn.color_changed.connect(self._apply)
        self._grad_end_btn = ColorSwatch(QColor(scene.backdrop_gradient_end))
        self._grad_end_btn.color_changed.connect(self._apply)
        grad_row.addWidget(QLabel("From:"))
        grad_row.addWidget(self._grad_start_btn)
        grad_row.addSpacing(8)
        grad_row.addWidget(QLabel("To:"))
        grad_row.addWidget(self._grad_end_btn)
        grad_row.addStretch()
        self._grad_row_widget = QWidget()
        self._grad_row_widget.setLayout(grad_row)
        form.addRow(self._grad_row_widget)

        # Padding
        self._padding_slider = QSlider(Qt.Orientation.Horizontal)
        self._padding_slider.setRange(0, 120)
        self._padding_slider.setValue(int(scene.backdrop_padding))
        self._padding_slider.valueChanged.connect(self._apply)
        self._padding_label = QLabel(f"{int(scene.backdrop_padding)} px")
        self._padding_label.setFixedWidth(42)
        pad_row = QHBoxLayout()
        pad_row.addWidget(self._padding_slider)
        pad_row.addWidget(self._padding_label)
        form.addRow("Padding:", pad_row)

        # Canvas corner radius
        images = scene.image_items()
        canvas_r = int(images[0].corner_radius()) if images else 0
        self._canvas_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self._canvas_radius_slider.setRange(0, 60)
        self._canvas_radius_slider.setValue(canvas_r)
        self._canvas_radius_slider.valueChanged.connect(self._apply)
        self._canvas_radius_label = QLabel(f"{canvas_r} px")
        self._canvas_radius_label.setFixedWidth(42)
        cr_row = QHBoxLayout()
        cr_row.addWidget(self._canvas_radius_slider)
        cr_row.addWidget(self._canvas_radius_label)
        form.addRow("Canvas radius:", cr_row)

        # Backdrop corner radius
        bd_r = int(scene.backdrop_corner_radius)
        self._backdrop_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self._backdrop_radius_slider.setRange(0, 60)
        self._backdrop_radius_slider.setValue(bd_r)
        self._backdrop_radius_slider.valueChanged.connect(self._apply)
        self._backdrop_radius_label = QLabel(f"{bd_r} px")
        self._backdrop_radius_label.setFixedWidth(42)
        br_row = QHBoxLayout()
        br_row.addWidget(self._backdrop_radius_slider)
        br_row.addWidget(self._backdrop_radius_label)
        form.addRow("Backdrop radius:", br_row)

        inner.addLayout(form)

        self._update_controls_enabled()
        self.setFixedWidth(300)

    # -- internal ----------------------------------------------------------

    def _apply(self) -> None:
        self._padding_label.setText(f"{self._padding_slider.value()} px")
        self._canvas_radius_label.setText(f"{self._canvas_radius_slider.value()} px")
        self._backdrop_radius_label.setText(f"{self._backdrop_radius_slider.value()} px")
        self._update_controls_enabled()

        self._scene.backdrop_enabled = self._enabled_check.isChecked()
        self._scene.backdrop_padding = self._padding_slider.value()
        self._scene.backdrop_corner_radius = self._backdrop_radius_slider.value()
        self._scene.canvas_corner_radius = self._canvas_radius_slider.value()

        if self._mode_gradient.isChecked():
            self._scene.backdrop_use_gradient = True
            self._scene.backdrop_gradient_start = self._grad_start_btn.color()
            self._scene.backdrop_gradient_end = self._grad_end_btn.color()
        else:
            self._scene.backdrop_use_gradient = False
            self._scene.backdrop_color = self._color_btn.color()

        for img in self._scene.image_items():
            img.set_corner_radius(self._canvas_radius_slider.value())

        self._view.viewport().update()

    def _update_controls_enabled(self) -> None:
        enabled = self._enabled_check.isChecked()
        use_colour = enabled and self._mode_colour.isChecked()
        use_grad = enabled and self._mode_gradient.isChecked()

        self._mode_colour.setEnabled(enabled)
        self._mode_gradient.setEnabled(enabled)

        # Show/hide colour vs gradient widgets
        self._color_btn.setVisible(use_colour)
        self._grad_row_widget.setVisible(use_grad)
        self._grad_start_btn.setEnabled(use_grad)
        self._grad_end_btn.setEnabled(use_grad)

        self._padding_slider.setEnabled(enabled)
        self._padding_label.setEnabled(enabled)
        self._canvas_radius_slider.setEnabled(enabled)
        self._canvas_radius_label.setEnabled(enabled)
        self._backdrop_radius_slider.setEnabled(enabled)
        self._backdrop_radius_label.setEnabled(enabled)

    # -- public ------------------------------------------------------------

    def show_below(self, widget: QWidget) -> None:
        pos = widget.mapToGlobal(QPoint(0, widget.height() + 4))
        screen = widget.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            if pos.x() + self.width() > geo.right():
                pos.setX(geo.right() - self.width() - 4)
            if pos.y() + self.height() > geo.bottom():
                pos.setY(widget.mapToGlobal(QPoint(0, -self.height() - 4)).y())
        self.move(pos)
        self.show()
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress and self.isVisible():
            mouse_event = event
            if not self.geometry().contains(mouse_event.globalPosition().toPoint()):
                self.hide()
                QApplication.instance().removeEventFilter(self)
                return False
        return super().eventFilter(watched, event)
