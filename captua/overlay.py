"""Frameless overlay window that displays the captured screenshot."""

# Pixels of checkerboard visible around the scene/backdrop when the window opens.
_VIEWPORT_MARGIN = 50

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsPixmapItem,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .backdrop import BackdropPopup
from .canvas import CanvasScene, CanvasView, draw_backdrop
from .settings import apply_to_scene, extract_from_scene, load_settings, save_settings
from .toolbar import Toolbar
from .tools import (
    ArrowTool,
    BlurTool,
    CounterTool,
    CropTool,
    EllipseTool,
    EmojiTool,
    LabelTool,
    LineTool,
    MagnifierTool,
    MarkerTool,
    PenTool,
    RectangleTool,
    RulerTool,
    SelectTool,
    ShapeTool,
    SpotlightTool,
    TextTool,
    ToolProperties,
)


class ToolbarScrollArea(QScrollArea):
    """Thin horizontal scroll wrapper that keeps the toolbar independent of window width."""

    def __init__(self, toolbar: "Toolbar", parent=None) -> None:
        super().__init__(parent)
        self.setWidget(toolbar)
        self.setWidgetResizable(False)
        self.setFixedHeight(80)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMinimumWidth(0)

    def wheelEvent(self, event) -> None:
        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() - event.angleDelta().y()
        )
        event.accept()


class OverlayWindow(QMainWindow):
    """
    A frameless, floating window for Hyprland/Wayland.

    Designed to work with these Hyprland windowrules:
        windowrule = float on, match:class ^(captua-overlay)$
        windowrule = center on, match:class ^(captua-overlay)$
        windowrule = pin on, match:class ^(captua-overlay)$
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Window flags for a clean overlay look
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Background colour (dark, modern)
        self.setStyleSheet("background-color: #18181B;")
        self.setAcceptDrops(True)

        # Central widget with vertical layout
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar wrapped in a scroll area so it doesn't force the window width
        self._toolbar = Toolbar(self)
        self._toolbar_scroll = ToolbarScrollArea(self._toolbar, self)
        layout.addWidget(self._toolbar_scroll)
        self.setMinimumWidth(self._toolbar.minimumSizeHint().width())
        self._backdrop_popup: BackdropPopup | None = None

        # Toast label for ephemeral status messages
        self._toast = QLabel(self)
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast.setStyleSheet(
            "background-color: #27272A; color: #F4F4F5; border-radius: 6px; padding: 6px 12px; font-size: 12px;"
        )
        self._toast.hide()

        # Canvas fills the rest of the window
        self._scene = CanvasScene(self)
        self._view = CanvasView(self._scene, self)
        layout.addWidget(self._view)

        # Tools
        self._props = ToolProperties()
        history = self._scene.history()
        self._tools = {
            "select": SelectTool(self._scene, self._props, history),
            "crop": CropTool(self._scene, self._props, history),
            "rectangle": RectangleTool(self._scene, self._props, history),
            "ellipse": EllipseTool(self._scene, self._props, history),
            "line": LineTool(self._scene, self._props, history),
            "arrow": ArrowTool(self._scene, self._props, history),
            "pen": PenTool(self._scene, self._props, history),
            "marker": MarkerTool(self._scene, self._props, history),
            "text": TextTool(self._scene, self._props, history),
            "label": LabelTool(self._scene, self._props, history),
            "counter": CounterTool(self._scene, self._props, history),
            "ruler": RulerTool(self._scene, self._props, history),
            "spotlight": SpotlightTool(self._scene, self._props, history),
            "blur": BlurTool(self._scene, self._props, history),
            "magnifier": MagnifierTool(self._scene, self._props, history),
            "shape": ShapeTool(self._scene, self._props, history),
            "emoji": EmojiTool(self._scene, self._props, history),
        }
        self._set_tool("select")

        # Load persisted settings
        self._settings = load_settings()
        apply_to_scene(self._scene, self._settings)

        # Apply default tool properties from settings
        self._props.color = QColor(self._settings.get("line_color", "#FF5D62"))
        self._props.stroke_width = self._settings.get("line_width", 3)
        self._props.fill_color = QColor(self._settings.get("fill_color", "#FF5D62"))
        self._props.fill_alpha = self._settings.get("fill_alpha", 128)
        self._toolbar.set_line_color(self._props.color)
        self._toolbar.set_line_width(self._props.stroke_width)
        self._toolbar.set_fill_color(self._props.fill_color)
        self._toolbar.set_fill_alpha(self._props.fill_alpha)

        # Toolbar signals
        self._toolbar.tool_changed.connect(self._set_tool)
        self._toolbar.line_color_changed.connect(self._update_line_color)
        self._toolbar.line_width_changed.connect(self._update_line_width)
        self._toolbar.fill_color_changed.connect(self._update_fill_color)
        self._toolbar.fill_alpha_changed.connect(self._update_fill_alpha)
        self._toolbar.shape_selected.connect(self._update_shape)
        self._toolbar.emoji_selected.connect(self._update_emoji)
        self._toolbar.close_triggered.connect(self.close)
        self._toolbar.save_triggered.connect(self.save_to_disk)
        self._toolbar.copy_triggered.connect(self.copy_to_clipboard)
        self._toolbar.import_image_triggered.connect(self._import_image)
        self._toolbar.capture_triggered.connect(self._capture_region)
        self._toolbar.backdrop_settings_triggered.connect(self._show_backdrop_dialog)
        self._toolbar.magnifier_zoom_changed.connect(self._update_magnifier_zoom)

        self._view.tool_finished.connect(lambda: self._set_tool("select"))
        self._view.tool_selected.connect(self._set_tool)
        self._scene.selectionChanged.connect(self._on_selection_changed)
        self._scene.sceneRectChanged.connect(self._on_scene_rect_changed)
        self._scene.scene_rect_fitted.connect(self._on_scene_rect_fitted)

    def _set_tool(self, name: str) -> None:
        tool = self._tools.get(name)
        self._view.set_active_tool(tool)
        self._toolbar.update_active_tool_button(name)
        # Show/hide properties based on whether the tool needs them
        self._toolbar.set_properties_visible(
            name not in ("select", "crop", "counter", "magnifier", "emoji", "shape")
        )

    def _update_line_color(self, color) -> None:
        self._props.color = color
        for item in self._scene.selectedItems():
            if item is self._scene.base_image():
                continue
            if hasattr(item, "set_line_color"):
                item.set_line_color(color)

    def _update_line_width(self, width: float) -> None:
        self._props.stroke_width = width
        for item in self._scene.selectedItems():
            if item is self._scene.base_image():
                continue
            if hasattr(item, "set_line_width"):
                item.set_line_width(width)

    def _update_fill_color(self, color) -> None:
        self._props.fill_color = color
        for item in self._scene.selectedItems():
            if item is self._scene.base_image():
                continue
            if hasattr(item, "set_fill_color"):
                item.set_fill_color(color)

    def _update_fill_alpha(self, alpha: int) -> None:
        self._props.fill_alpha = alpha
        for item in self._scene.selectedItems():
            if item is self._scene.base_image():
                continue
            if hasattr(item, "set_fill_alpha"):
                item.set_fill_alpha(alpha)

    def _on_selection_changed(self) -> None:
        items = [i for i in self._scene.selectedItems() if i is not self._scene.base_image()]
        if len(items) != 1:
            self._toolbar.set_properties_visible(
                self._toolbar.active_tool() not in ("select", "crop", "counter", "magnifier", "emoji", "shape")
            )
            return
        item = items[0]
        if hasattr(item, "line_color"):
            self._toolbar.set_line_color(item.line_color())
            self._props.color = item.line_color()
        if hasattr(item, "line_width"):
            self._toolbar.set_line_width(item.line_width())
            self._props.stroke_width = item.line_width()
        if hasattr(item, "fill_color"):
            self._toolbar.set_fill_color(item.fill_color())
            self._props.fill_color = item.fill_color()
        if hasattr(item, "fill_alpha"):
            self._toolbar.set_fill_alpha(item.fill_alpha())
            self._props.fill_alpha = item.fill_alpha()
        if hasattr(item, "zoom_level"):
            self._toolbar.set_magnifier_zoom(item.zoom_level())
            self._props.zoom_level = item.zoom_level()
        self._toolbar.set_properties_visible(True)

    def _update_shape(self, shape_type: str) -> None:
        self._props.shape_type = shape_type

    def _update_emoji(self, emoji: str) -> None:
        self._props.emoji = emoji

    def _update_magnifier_zoom(self, zoom: float) -> None:
        self._props.zoom_level = zoom
        for item in self._scene.selectedItems():
            if item is self._scene.base_image():
                continue
            if hasattr(item, "set_zoom_level"):
                item.set_zoom_level(zoom)

    def _capture_region(self) -> None:
        """Capture a new region and add it to the canvas."""
        try:
            from .capture import capture_region
            pixmap = capture_region()
            if pixmap is not None and not pixmap.isNull():
                try:
                    dpr = self.screen().devicePixelRatio()
                except Exception:
                    dpr = 1.0
                pixmap.setDevicePixelRatio(dpr)
                center = self._view.mapToScene(self._view.viewport().rect().center())
                pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                self._scene.add_image(pixmap, pos)
        except RuntimeError:
            pass  # User cancelled or capture failed

    def _import_image(self) -> None:
        """Open a file dialog to import an image onto the canvas."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)",
        )
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Place at center of current view
                center = self._view.mapToScene(self._view.viewport().rect().center())
                pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                self._scene.add_image(pixmap, pos)

    def paste_from_clipboard(self) -> None:
        """Paste image from clipboard onto the canvas."""
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime is None:
            return

        # Try image data first
        if mime.hasImage():
            from PySide6.QtGui import QImage
            img = mime.imageData()
            if isinstance(img, QImage):
                pixmap = QPixmap.fromImage(img)
                if not pixmap.isNull():
                    center = self._view.mapToScene(self._view.viewport().rect().center())
                    pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                    self._scene.add_image(pixmap, pos)
                    return

        # Try URLs
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    pixmap = QPixmap(url.toLocalFile())
                    if not pixmap.isNull():
                        center = self._view.mapToScene(self._view.viewport().rect().center())
                        pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                        self._scene.add_image(pixmap, pos)
                        return

    def _show_backdrop_dialog(self) -> None:
        """Show backdrop settings popup below toolbar button."""
        self._backdrop_popup = BackdropPopup(self._scene, self._view)
        self._backdrop_popup.show_below(self._toolbar.backdrop_button())

    def set_crop_mode(self, enabled: bool) -> None:
        """Hide toolbar and activate crop tool; called for region/window modes."""
        if enabled:
            self._toolbar.hide()
            self._set_tool("crop")
            self._toolbar.set_tool("crop")
        else:
            self._toolbar.show()
            self._set_tool("select")
            self._toolbar.set_tool("select")

    def _screen_constraints(self) -> tuple[int, int, int, int]:
        """Return (margin, max_w, max_h) for window sizing."""
        try:
            screen = self.screen().geometry()
        except Exception:
            screen = None
        margin = 50
        if screen is not None:
            max_w = int(screen.width() * 0.9)
            max_h = int(screen.height() * 0.9)
        else:
            max_w = 1920
            max_h = 1080
        return margin, max_w, max_h

    def _resize_for_scene(self) -> None:
        """Resize window to show scene rect plus checkerboard margin on all sides."""
        _, max_w, max_h = self._screen_constraints()
        scene_rect = self._scene.sceneRect()
        needed_w = int(scene_rect.width()) + _VIEWPORT_MARGIN * 2
        needed_h = int(scene_rect.height()) + 80 + _VIEWPORT_MARGIN * 2
        new_w = max(needed_w, self.minimumWidth())
        new_h = min(max(needed_h, 0), max_h)
        self.resize(new_w, new_h)

    def _on_scene_rect_changed(self, rect: QRectF) -> None:
        """Scene rect changed — resizing is handled by _on_scene_rect_fitted."""
        pass

    def _on_scene_rect_fitted(self, old_rect: QRectF, new_rect: QRectF) -> None:
        """Resize window to keep the new scene rect visible with checkerboard margin."""
        _, max_w, max_h = self._screen_constraints()
        needed_w = int(new_rect.width()) + _VIEWPORT_MARGIN * 2
        needed_h = int(new_rect.height()) + 80 + _VIEWPORT_MARGIN * 2
        new_w = max(needed_w, self.minimumWidth())
        new_h = min(max(needed_h, 0), max_h)
        self.resize(new_w, new_h)
        self._view.viewport().update()

    def set_image(self, pixmap: QPixmap) -> None:
        """Load a new screenshot into the canvas."""
        # Apply screen DPR so the pixmap renders 1:1 with physical pixels
        try:
            dpr = self.screen().devicePixelRatio()
        except Exception:
            dpr = 1.0
        pixmap.setDevicePixelRatio(dpr)

        self._scene.set_base_image(pixmap)
        self._resize_for_scene()
        if self.isVisible():
            self._fit_image()

    def _fit_image(self) -> None:
        """Show scene at 1:1 centered (margin visible) or scaled if screen-capped."""
        scene_rect = self._scene.sceneRect()
        view_rect = self._view.viewport().rect()
        if scene_rect.width() <= view_rect.width() and scene_rect.height() <= view_rect.height():
            # Fits at 1:1 — window was sized with margin, so checkerboard shows around it
            self._view.resetTransform()
            self._view.centerOn(scene_rect.center())
        else:
            # Screen-capped window: scale to fit, keep margin where possible
            scale = min(
                max((view_rect.width() - _VIEWPORT_MARGIN * 2), 1) / scene_rect.width(),
                max((view_rect.height() - _VIEWPORT_MARGIN * 2), 1) / scene_rect.height(),
            )
            self._view.resetTransform()
            self._view.scale(scale, scale)
            self._view.centerOn(scene_rect.center())

    def showEvent(self, event) -> None:
        """Defer fitting until the viewport has a real size."""
        super().showEvent(event)
        if self._scene.base_image() is not None:
            self._fit_image()

    def closeEvent(self, event) -> None:
        """Persist all current settings on window close."""
        stored = {**extract_from_scene(self._scene)}
        stored["line_color"] = self._props.color.name()
        stored["line_width"] = self._props.stroke_width
        stored["fill_color"] = self._props.fill_color.name()
        stored["fill_alpha"] = self._props.fill_alpha
        save_settings(stored)
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

    def add_capture(self, pixmap: QPixmap, direction: str = "vertical") -> None:
        """Stitch a new capture onto the existing canvas."""
        base = self._scene.base_image()
        if base is None:
            self._scene.set_base_image(pixmap)
            return

        if direction == "vertical":
            # Place below the existing base image
            pos = QPointF(base.x(), base.y() + base.pixmap().height())
        else:
            # Place to the right
            pos = QPointF(base.x() + base.pixmap().width(), base.y())

        self._scene.add_image(pixmap, pos)

    def render_to_pixmap(self) -> QPixmap:
        """Render the entire scene (with backdrop) to a pixmap at physical resolution."""
        base = self._scene.base_image()
        dpr = base.pixmap().devicePixelRatio() if base else 1.0

        # Full bounds of all items, plus backdrop padding
        items_rect = self._scene.itemsBoundingRect()
        pad = self._scene.backdrop_padding
        render_rect = items_rect.adjusted(-pad, -pad, pad, pad)

        physical_w = max(1, int(render_rect.width() * dpr))
        physical_h = max(1, int(render_rect.height() * dpr))
        pixmap = QPixmap(physical_w, physical_h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = None
        try:
            from PySide6.QtGui import QPainter
            painter = QPainter(pixmap)
            painter.scale(dpr, dpr)
            painter.save()
            painter.translate(-render_rect.x(), -render_rect.y())
            draw_backdrop(painter, self._scene, self._scene._content_rect)
            painter.restore()
            # Hide selection decorations during export
            selected = list(self._scene.selectedItems())
            for item in selected:
                item.setSelected(False)
            # Render scene items on top
            self._scene.render(painter, QRectF(0, 0, render_rect.width(), render_rect.height()), render_rect)
            # Restore selection
            for item in selected:
                item.setSelected(True)
        finally:
            if painter is not None:
                painter.end()
        return pixmap

    def _save_pixmap_auto(self, pixmap: QPixmap) -> Path | None:
        """Save pixmap to the configured screenshots folder. Returns the path or None on failure."""
        folder = Path(self._settings.get("screenshots_folder", "~/Pictures/Screenshots")).expanduser()
        folder.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        template = self._settings.get("screenshot_filename_template", "captua-{timestamp}.png")
        filename = template.replace("{timestamp}", ts).replace("{date}", datetime.now().strftime("%Y-%m-%d"))
        path = folder / filename

        if pixmap.save(str(path), "PNG"):
            return path
        return None

    def _show_toast(self, message: str, duration_ms: int = 1500) -> None:
        """Show a transient status label centered in the window."""
        from PySide6.QtWidgets import QLabel
        if self._toast is None:
            self._toast = QLabel(self)
            self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._toast.setStyleSheet(
                "background-color: #27272A; color: #F4F4F5; border-radius: 6px; padding: 6px 12px; font-size: 12px;"
            )
        self._toast.setText(message)
        self._toast.adjustSize()
        x = (self.width() - self._toast.width()) // 2
        y = self.height() - self._toast.height() - 20
        self._toast.move(x, y)
        self._toast.raise_()
        self._toast.show()
        QTimer.singleShot(duration_ms, self._toast.hide)

    def copy_to_clipboard(self) -> None:
        """Render scene, copy to clipboard, auto-save, and optionally close."""
        pixmap = self.render_to_pixmap()
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setPixmap(pixmap)

        auto_save = self._settings.get("auto_save_on_copy", True)
        if auto_save:
            saved_path = self._save_pixmap_auto(pixmap)
            if saved_path is not None:
                self._show_toast(f"Saved to {saved_path.name}", 1200)
                # Delay close so the toast is visible briefly
                QTimer.singleShot(1400, self.close)
            else:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    "Could not auto-save the screenshot. Please use Save As (Ctrl+S) instead.",
                )
        else:
            self.close()

    def save_to_disk(self) -> None:
        """Render scene and save to a user-selected file."""
        from PySide6.QtWidgets import QFileDialog
        pixmap = self.render_to_pixmap()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            "captua-screenshot.png",
            "Images (*.png *.jpg *.webp)",
        )
        if file_path:
            pixmap.save(file_path)

