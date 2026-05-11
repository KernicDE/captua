"""High-performance canvas built on QGraphicsScene."""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QKeyEvent,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

from .history import History, RemoveItemCommand
from .items import CanvasImageItem, MagnifierCalloutItem


def draw_backdrop(painter: QPainter, scene: "CanvasScene", images_rect: QRectF) -> None:
    """Paint the backdrop rectangle behind images."""
    if images_rect.isEmpty():
        return
    pad = scene.backdrop_padding
    if pad <= 0:
        return
    r = images_rect.adjusted(-pad, -pad, pad, pad)
    painter.setPen(Qt.PenStyle.NoPen)
    if scene.backdrop_use_gradient:
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0, scene.backdrop_gradient_start)
        grad.setColorAt(1, scene.backdrop_gradient_end)
        painter.setBrush(grad)
    else:
        painter.setBrush(scene.backdrop_color)
    radius = scene.backdrop_corner_radius
    if radius > 0:
        painter.drawRoundedRect(r, radius, radius)
    else:
        painter.drawRect(r)


class CanvasScene(QGraphicsScene):
    """Scene that holds screenshots and annotation layers."""

    scene_rect_fitted = Signal(QRectF, QRectF)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._base_item: CanvasImageItem | None = None
        self._image_items: list[CanvasImageItem] = []
        self._history = History()
        self._content_rect = QRectF()

        # Backdrop / canvas appearance settings (drawn by CanvasView)
        self.backdrop_padding = 20
        self.backdrop_color = QColor("#2A2A37")
        self.backdrop_use_gradient = False
        self.backdrop_gradient_start = QColor("#2A2A37")
        self.backdrop_gradient_end = QColor("#1F1F28")
        self.backdrop_corner_radius = 0.0
        self.canvas_corner_radius = 0.0

    def history(self) -> History:
        return self._history

    def set_base_image(self, pixmap) -> None:
        """Set or replace the background screenshot."""
        if self._base_item is not None:
            self.removeItem(self._base_item)
            self._base_item = None

        self._base_item = CanvasImageItem(pixmap)
        self._base_item.setZValue(0)
        self._base_item.set_corner_radius(self.canvas_corner_radius)
        self.addItem(self._base_item)
        self._content_rect = self._base_item.boundingRect()
        pad = max(self.backdrop_padding, 25)
        self.setSceneRect(self._content_rect.adjusted(-pad, -pad, pad, pad))

    def base_image(self):
        """Return the current base image item, or None."""
        return self._base_item

    def add_image(self, pixmap, pos=None) -> CanvasImageItem:
        """Add an additional image to the canvas."""
        item = CanvasImageItem(pixmap)
        item.setZValue(0)
        item.set_corner_radius(self.canvas_corner_radius)
        if pos is not None:
            item.setPos(pos)
        self.addItem(item)
        self._image_items.append(item)
        self._expand_scene_if_needed()
        self.update()
        return item

    def image_items(self) -> list[CanvasImageItem]:
        """Return all image items including the base image."""
        items: list[CanvasImageItem] = []
        if self._base_item is not None:
            items.append(self._base_item)
        items.extend(self._image_items)
        return items

    def image_content_rect(self) -> QRectF:
        """Bounding rect of all image items (screenshots), ignoring annotations."""
        rect = QRectF()
        for item in self.image_items():
            rect = rect.united(item.mapRectToScene(item.boundingRect()))
        return rect

    def _expand_scene_if_needed(self) -> None:
        """Fit scene rect tightly around all items with minimum 25 px padding."""
        old_rect = self.sceneRect()
        items_rect = QRectF()
        for item in self.items():
            items_rect = items_rect.united(item.mapRectToScene(item.boundingRect()))
        self._content_rect = items_rect
        padding = max(self.backdrop_padding, 25)
        new_rect = items_rect.adjusted(-padding, -padding, padding, padding)
        # Ensure a non-empty rect even when no items are present
        if new_rect.isEmpty():
            new_rect = QRectF(-padding, -padding, padding * 2, padding * 2)
        if old_rect != new_rect:
            self.setSceneRect(new_rect)
            # Invalidate union so shrinking also clears the old backdrop area.
            self.invalidate(old_rect.united(new_rect), QGraphicsScene.SceneLayer.BackgroundLayer)
            for view in self.views():
                view.viewport().update()
            self.scene_rect_fitted.emit(old_rect, new_rect)


class CanvasView(QGraphicsView):
    """View with zoom, pan, tool routing, and shortcut handling."""

    tool_finished = Signal()
    tool_selected = Signal(str)

    def __init__(self, scene: CanvasScene, parent=None) -> None:
        super().__init__(scene, parent)
        self._zoom = 1.0
        self._panning = False
        self._pan_start = None
        self._active_tool = None

        # Resize handle state (active in SelectTool mode)
        self._resize_item = None
        self._resize_handle = None
        self._resize_start_local = None
        self._resize_start_rect = None

        # Magnifier glass drag state
        self._glass_item = None
        self._glass_start_scene = None
        self._glass_dest_start = None

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setMouseTracking(True)

        # Frameless look; scrollbars remain functional (for panning) but are hidden via CSS.
        # ScrollBarAlwaysOff would force the range to 0, breaking middle-button pan.
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalScrollBar().setStyleSheet("QScrollBar:horizontal { height: 0px; }")
        self.verticalScrollBar().setStyleSheet("QScrollBar:vertical { width: 0px; }")
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setAcceptDrops(True)

        scene.selectionChanged.connect(self.viewport().update)

    def set_active_tool(self, tool) -> None:
        """Set the current annotation tool."""
        if self._active_tool is not None:
            self._active_tool.deactivate()
        self._active_tool = tool
        if self._active_tool is not None:
            self._active_tool.activate()
        # Ensure the view has focus when returning to select mode so
        # keyboard shortcuts keep working (unless a text item is being edited).
        if self._active_tool is not None and not self._active_tool.handles_mouse:
            scene = self.scene()
            if scene is not None and scene.focusItem() is None:
                self.setFocus()

    def _scene_pos(self, event: QMouseEvent):
        """Map viewport mouse position to scene coordinates."""
        return self.mapToScene(event.pos())

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Ctrl+wheel zooms; plain wheel scrolls vertically."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1 / 1.15
            self._zoom *= factor
            self.scale(factor, factor)
            self.viewport().update()
            event.accept()
        else:
            super().wheelEvent(event)

    def drawBackground(self, painter: QPainter, rect) -> None:
        # 1. Checkerboard
        cell = 20
        c1 = QColor("#363646")
        c2 = QColor("#2A2A37")
        x_start = int(rect.left()) // cell * cell
        y_start = int(rect.top()) // cell * cell
        for y in range(y_start, int(rect.bottom()) + cell, cell):
            for x in range(x_start, int(rect.right()) + cell, cell):
                color = c1 if ((x // cell) + (y // cell)) % 2 == 0 else c2
                painter.fillRect(x, y, cell, cell, color)

        # 2. Backdrop behind all content
        scene = self.scene()
        if scene is None:
            return
        draw_backdrop(painter, scene, scene._content_rect)

    def _tool_handles_mouse(self) -> bool:
        return self._active_tool is not None and self._active_tool.handles_mouse

    def _item_supports_resize(self, item) -> bool:
        return hasattr(item, "setRect") and not hasattr(item, "_points")

    def _item_rect(self, item) -> QRectF:
        if hasattr(item, "rect"):
            return item.rect()
        return item.boundingRect()

    def _hit_resize_handle(self, viewport_pos):
        if self._active_tool is None or self._active_tool.handles_mouse:
            return None, None
        scene_pos = self.mapToScene(viewport_pos)
        scale = self.transform().m11()
        hit_dist = max(8 / scale, 2)
        for item in self.scene().selectedItems():
            if not self._item_supports_resize(item):
                continue
            r = self._item_rect(item)
            handles = {
                "tl": item.mapToScene(r.topLeft()),
                "tr": item.mapToScene(r.topRight()),
                "bl": item.mapToScene(r.bottomLeft()),
                "br": item.mapToScene(r.bottomRight()),
            }
            for name, point in handles.items():
                if abs(scene_pos.x() - point.x()) < hit_dist and abs(scene_pos.y() - point.y()) < hit_dist:
                    return item, name
        return None, None

    def _handle_cursor(self, handle: str):
        mapping = {
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
        }
        return mapping.get(handle, Qt.CursorShape.ArrowCursor)

    def _do_resize(self, scene_pos: QPointF) -> None:
        item = self._resize_item
        handle = self._resize_handle
        local_pos = item.mapFromScene(scene_pos)
        r = self._resize_start_rect
        x1, y1, x2, y2 = r.left(), r.top(), r.right(), r.bottom()
        if "l" in handle:
            x1 = local_pos.x()
        if "r" in handle:
            x2 = local_pos.x()
        if "t" in handle:
            y1 = local_pos.y()
        if "b" in handle:
            y2 = local_pos.y()
        new_rect = QRectF(x1, y1, x2 - x1, y2 - y1).normalized()
        if new_rect.width() < 4:
            new_rect.setWidth(4)
        if new_rect.height() < 4:
            new_rect.setHeight(4)
        item.setRect(new_rect)

    def _hit_magnifier_glass(self, viewport_pos):
        if self._active_tool is None or self._active_tool.handles_mouse:
            return None
        scene_pos = self.mapToScene(viewport_pos)
        scale = self.transform().m11()
        hit_dist = max(8 / scale, 2)
        for item in self.scene().selectedItems():
            if not isinstance(item, MagnifierCalloutItem):
                continue
            dest = item.mapToScene(item._dest_c)
            dx = scene_pos.x() - dest.x()
            dy = scene_pos.y() - dest.y()
            if dx * dx + dy * dy <= (item._dest_r + hit_dist) ** 2:
                return item
        return None

    def _do_glass_drag(self, scene_pos: QPointF) -> None:
        item = self._glass_item
        delta = scene_pos - self._glass_start_scene
        # _glass_dest_start is a local coordinate; delta is in scene space.
        # Since the item has no rotation/scale, scene delta == local delta.
        item.prepareGeometryChange()
        item._dest_c = self._glass_dest_start + delta
        item.update()

    def drawForeground(self, painter: QPainter, rect) -> None:
        super().drawForeground(painter, rect)
        if self._active_tool is None or self._active_tool.handles_mouse:
            return
        scale = self.transform().m11()
        handle_size = max(8 / scale, 2)
        pen_width = max(1 / scale, 0.5)
        painter.setPen(QPen(QColor("#7E9CD8"), pen_width))
        painter.setBrush(QColor("#7E9CD8"))
        for item in self.scene().selectedItems():
            if not self._item_supports_resize(item):
                continue
            r = self._item_rect(item)
            for corner in [
                item.mapToScene(r.topLeft()),
                item.mapToScene(r.topRight()),
                item.mapToScene(r.bottomLeft()),
                item.mapToScene(r.bottomRight()),
            ]:
                painter.drawRect(
                    corner.x() - handle_size / 2,
                    corner.y() - handle_size / 2,
                    handle_size,
                    handle_size,
                )
        # Draw glass drag handle for selected magnifiers
        for item in self.scene().selectedItems():
            if not isinstance(item, MagnifierCalloutItem):
                continue
            dest = item.mapToScene(item._dest_c)
            painter.setPen(QPen(QColor("#7E9CD8"), pen_width))
            painter.setBrush(QColor("#7E9CD8"))
            painter.drawRect(
                dest.x() - handle_size / 2,
                dest.y() - handle_size / 2,
                handle_size,
                handle_size,
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool_handles_mouse():
            self._active_tool.mouse_press(event, self._scene_pos(event))
            event.accept()
            return
        item, handle = self._hit_resize_handle(event.pos())
        if item is not None:
            self._resize_item = item
            self._resize_handle = handle
            self._resize_start_local = item.mapFromScene(self._scene_pos(event))
            self._resize_start_rect = QRectF(self._item_rect(item))
            event.accept()
            return
        glass_item = self._hit_magnifier_glass(event.pos())
        if glass_item is not None:
            self._glass_item = glass_item
            self._glass_start_scene = self._scene_pos(event)
            self._glass_dest_start = QPointF(glass_item._dest_c)
            event.accept()
            return
        super().mousePressEvent(event)

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        """Override to force a full viewport repaint after any scroll."""
        super().scrollContentsBy(dx, dy)
        self.viewport().update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._panning and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return
        if self._resize_item is not None:
            self._do_resize(self._scene_pos(event))
            event.accept()
            return
        if self._glass_item is not None:
            self._do_glass_drag(self._scene_pos(event))
            event.accept()
            return
        if self._tool_handles_mouse():
            self._active_tool.mouse_move(event, self._scene_pos(event))
            event.accept()
            return
        item, handle = self._hit_resize_handle(event.pos())
        if item is not None:
            self.setCursor(self._handle_cursor(handle))
            return
        glass_item = self._hit_magnifier_glass(event.pos())
        if glass_item is not None:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            return
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self._pan_start = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._resize_item is not None:
            self._resize_item = None
            self._resize_handle = None
            self._resize_start_local = None
            self._resize_start_rect = None
            self.scene()._expand_scene_if_needed()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._glass_item is not None:
            self._glass_item = None
            self._glass_start_scene = None
            self._glass_dest_start = None
            self.scene()._expand_scene_if_needed()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool_handles_mouse():
            self._active_tool.mouse_release(event, self._scene_pos(event))
            event.accept()
            if self._active_tool.__class__.__name__ not in ("SelectTool", "CropTool", "CounterTool"):
                self.tool_finished.emit()
            self.scene()._expand_scene_if_needed()
            self.viewport().update()
            return
        super().mouseReleaseEvent(event)
        self.scene()._expand_scene_if_needed()
        self.viewport().update()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        scene = self.scene()
        pos = self.mapToScene(event.pos())
        handled = False

        # Try image data first
        mime = event.mimeData()
        if mime.hasImage():
            from PySide6.QtGui import QImage
            img = mime.imageData()
            if isinstance(img, QImage):
                pixmap = QPixmap.fromImage(img)
                if not pixmap.isNull():
                    scene.add_image(pixmap, pos)
                    handled = True

        # Try URLs
        if not handled and mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    pixmap = QPixmap(url.toLocalFile())
                    if not pixmap.isNull():
                        scene.add_image(pixmap, pos)
                        handled = True
                        break

        if handled:
            event.acceptProposedAction()
        else:
            event.ignore()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # When a text item is being edited, let it handle all keys — don't
        # intercept tool shortcuts like R, T, etc.
        scene = self.scene()
        if scene is not None:
            focused = scene.focusItem()
            if isinstance(focused, QGraphicsTextItem):
                super().keyPressEvent(event)
                return

        # Tool shortcuts — mirror the toolbar so they work when the canvas has focus
        tool_keys = {
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
        if event.key() in tool_keys and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.tool_selected.emit(tool_keys[event.key()])
            event.accept()
            return

        if event.key() == Qt.Key.Key_Escape:
            # If a text item has focus, clear focus instead of closing
            focused = self.scene().focusItem()
            if focused is not None:
                focused.clearFocus()
                event.accept()
                return
            self.window().close()
            event.accept()
        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            scene = self.scene()
            for item in list(scene.selectedItems()):
                if item is not scene.base_image():
                    scene.history().push(RemoveItemCommand(scene, item))
            event.accept()
        elif event.key() == Qt.Key.Key_PageUp:
            for item in self.scene().selectedItems():
                if item is not self.scene().base_image():
                    item.setZValue(item.zValue() + 1)
            self.scene().update()
            event.accept()
        elif event.key() == Qt.Key.Key_PageDown:
            for item in self.scene().selectedItems():
                if item is not self.scene().base_image() and item.zValue() > 0.1:
                    item.setZValue(item.zValue() - 1)
            self.scene().update()
            event.accept()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.scene().history().redo()
            else:
                self.scene().history().undo()
            event.accept()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.scene().history().redo()
            event.accept()
        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            win = self.window()
            if hasattr(win, "copy_to_clipboard"):
                win.copy_to_clipboard()
            event.accept()
        elif event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            win = self.window()
            if hasattr(win, "paste_from_clipboard"):
                win.paste_from_clipboard()
            event.accept()
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            win = self.window()
            if hasattr(win, "save_to_disk"):
                win.save_to_disk()
            event.accept()
        else:
            super().keyPressEvent(event)
