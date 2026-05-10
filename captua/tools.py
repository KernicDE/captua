"""Annotation tools."""

import logging
import math
from io import BytesIO

from PIL import Image, ImageChops, ImageDraw, ImageFilter, UnidentifiedImageError
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap, QTextCursor

from .history import AddItemCommand
from .items import (
    ArrowItem,
    BlurItem,
    CounterItem,
    CropOverlayItem,
    EllipseItem,
    EmojiItem,
    LabelItem,
    LineItem,
    MagnifierCalloutItem,
    MarkerItem,
    PenItem,
    RectangleItem,
    RulerItem,
    ShapeItem,
    SpotlightItem,
    TextItem,
)


class ToolProperties:
    """Shared drawing properties."""

    def __init__(self) -> None:
        self.color = QColor("#FF5D62")  # Default red (line color)
        self.stroke_width = 3.0
        self.rounded_radius = 6.0
        self.font_size = 16
        self.counter = 1
        self.shape_type = "heart"
        self.shape_filled = False
        self.fill_color = QColor("#FF5D62")
        self.fill_alpha = 128
        self.emoji = "😀"
        self.zoom_level = 2.0


class Tool:
    """Base class for annotation tools."""

    handles_mouse = True

    def __init__(self, scene, properties: ToolProperties, history) -> None:
        self.scene = scene
        self.props = properties
        self.history = history
        self._active_item = None

    def activate(self) -> None:
        pass

    def deactivate(self) -> None:
        if self._active_item is not None:
            self._active_item = None

    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        pass

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        pass

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        pass

    def _push_add(self, item) -> None:
        if self.history is not None and item is not None:
            self.history.push(AddItemCommand(self.scene, item))


class SelectTool(Tool):
    """Default tool — no-op for drawing, lets the view handle selection."""

    handles_mouse = False


class CropTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        overlay = self.scene.sceneRect()
        self._active_item = CropOverlayItem(overlay, QRectF(pos, pos))
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.set_crop(QRectF(self._start, pos).normalized())

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            crop_rect = self._active_item.crop_rect.normalized()
            self.scene.removeItem(self._active_item)
            self._active_item = None
            base = self.scene.base_image()
            if base is not None:
                pixmap = base.pixmap()
                dpr = pixmap.devicePixelRatio()
                # Crop in logical coordinates, copy handles DPR
                cropped = pixmap.copy(
                    int(crop_rect.x()),
                    int(crop_rect.y()),
                    max(1, int(crop_rect.width())),
                    max(1, int(crop_rect.height())),
                )
                if not cropped.isNull():
                    cropped.setDevicePixelRatio(dpr)
                    # Remove all annotations and clear history
                    for item in list(self.scene.items()):
                        if item is not base:
                            self.scene.removeItem(item)
                    if self.history is not None:
                        self.history.clear()
                    # Replace base image
                    self.scene.set_base_image(cropped)
                    # Resize window via overlay
                    win = None
                    for view in self.scene.views():
                        win = view.window()
                        break
                    if win is not None and hasattr(win, "set_image"):
                        win.set_image(cropped)
                        win._fit_image()
                        # Exit crop mode: show toolbar and switch to select
                        if hasattr(win, "set_crop_mode"):
                            win.set_crop_mode(False)


class RectangleTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        self._active_item = RectangleItem(
            QRectF(pos, pos),
            self.props.color,
            self.props.stroke_width,
            self.props.rounded_radius,
            self.props.fill_color,
            self.props.fill_alpha,
        )
        self._active_item.setZValue(1)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            rect = QRectF(self._start, pos).normalized()
            self._active_item.setRect(rect)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class EllipseTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._center = pos
        self._active_item = EllipseItem(
            QRectF(pos, pos),
            self.props.color,
            self.props.stroke_width,
            self.props.fill_color,
            self.props.fill_alpha,
        )
        self._active_item.setZValue(1)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            dx = abs(pos.x() - self._center.x())
            dy = abs(pos.y() - self._center.y())
            rect = QRectF(self._center.x() - dx, self._center.y() - dy, dx * 2, dy * 2)
            self._active_item.setRect(rect)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class LineTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        self._active_item = LineItem(pos, pos, self.props.color, self.props.stroke_width)
        self._active_item.setZValue(1)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.setLine(self._start.x(), self._start.y(), pos.x(), pos.y())

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class ArrowTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        self._active_item = ArrowItem(pos, pos, self.props.color, self.props.stroke_width)
        self._active_item.setZValue(1)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.set_end(pos)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class PenTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._active_item = PenItem(self.props.color, self.props.stroke_width)
        self._active_item.setZValue(1)
        self._active_item.add_point(pos)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.add_point(pos)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class MarkerTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._active_item = MarkerItem(self.props.fill_color, self.props.fill_alpha, self.props.stroke_width * 4)
        self._active_item.setZValue(0.5)
        self._active_item.add_point(pos)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.add_point(pos)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class TextTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        item = TextItem(pos, self.props.color)
        item.setZValue(1)
        self.scene.addItem(item)
        item.setFocus()
        self._push_add(item)
        self.scene._expand_scene_if_needed()


class CounterTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        item = CounterItem(pos, self.props.counter, self.props.color)
        self.props.counter += 1
        self.scene.addItem(item)
        self._push_add(item)
        self.scene._expand_scene_if_needed()


class ShapeTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._center = pos
        self._active_item = ShapeItem(
            QRectF(pos, pos),
            self.props.shape_type,
            self.props.color,
            self.props.stroke_width,
            self.props.fill_color,
            self.props.fill_alpha,
            True,
        )
        self._active_item.setZValue(1)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            dx = abs(pos.x() - self._center.x())
            dy = abs(pos.y() - self._center.y())
            rect = QRectF(self._center.x() - dx, self._center.y() - dy, dx * 2, dy * 2)
            self._active_item.setRect(rect)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class EmojiTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._center = pos
        self._active_item = EmojiItem(QRectF(pos, pos), self.props.emoji)
        self._active_item.setZValue(1)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            dx = abs(pos.x() - self._center.x())
            dy = abs(pos.y() - self._center.y())
            rect = QRectF(self._center.x() - dx, self._center.y() - dy, dx * 2, dy * 2)
            self._active_item.setRect(rect)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class LabelTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        item = LabelItem(pos, self.props.color)
        item.setZValue(1)
        self.scene.addItem(item)
        item.setFocus(Qt.FocusReason.MouseFocusReason)
        tc = item.textCursor()
        tc.select(QTextCursor.SelectionType.Document)
        item.setTextCursor(tc)
        self._push_add(item)
        self.scene._expand_scene_if_needed()


class RulerTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        self._active_item = RulerItem(pos, pos, self.props.color, self.props.stroke_width)
        self._active_item.setZValue(1)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.set_end(pos)

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class SpotlightTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        overlay = self.scene.sceneRect()
        self._active_item = SpotlightItem(
            overlay,
            QRectF(pos, pos),
            self.props.fill_color,
            self.props.fill_alpha,
        )
        self._active_item.setZValue(0.8)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.set_spotlight(QRectF(self._start, pos).normalized())

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._push_add(self._active_item)
            self._active_item = None


class BlurTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        self._active_item = RectangleItem(
            QRectF(pos, pos), QColor("#DCD7BA"), 1, 0
        )
        self._active_item.setZValue(1)
        self._active_item.setOpacity(0.5)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.setRect(QRectF(self._start, pos).normalized())

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            rect = self._active_item.rect()
            self.scene.removeItem(self._active_item)
            self._active_item = None
            result = self._blur_region(rect)
            if result is not None:
                blurred, offset, pad = result
                if not blurred.isNull():
                    item = BlurItem(rect, blurred, offset, pad)
                    self.scene.addItem(item)
                    self._push_add(item)

    def _blur_region(self, rect: QRectF) -> tuple[QPixmap, QPointF, int] | None:
        try:
            pad = 10
            x = max(0, int(rect.x()) - pad)
            y = max(0, int(rect.y()) - pad)
            w = max(1, int(rect.width()) + pad * 2)
            h = max(1, int(rect.height()) + pad * 2)
            rw = int(rect.width())
            rh = int(rect.height())

            scene_pixmap = QPixmap(w, h)
            scene_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(scene_pixmap)
            self.scene.render(painter, QRectF(0, 0, w, h), QRectF(x, y, w, h))
            painter.end()

            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            scene_pixmap.save(buf, "PNG")
            buf.close()

            pil_img = Image.open(BytesIO(bytes(ba))).convert("RGBA")
            pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=25))

            # Feather mask: white over original selection, fading to black in padding
            mask = Image.new("L", (w, h), 0)
            draw = ImageDraw.Draw(mask)
            draw.rectangle([pad, pad, pad + rw, pad + rh], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=pad))

            r, g, b, a = pil_img.split()
            a = ImageChops.multiply(a, mask)
            pil_img = Image.merge("RGBA", (r, g, b, a))

            out_buf = BytesIO()
            pil_img.save(out_buf, format="PNG")
            result = QPixmap()
            result.loadFromData(QByteArray(out_buf.getvalue()))
            offset = QPointF(-pad, -pad)
            return result, offset, pad
        except (OSError, UnidentifiedImageError, ValueError):
            logging.exception("BlurTool._blur_region failed")
            return None


class MagnifierTool(Tool):
    def mouse_press(self, event: QMouseEvent, pos: QPointF) -> None:
        self._start = pos
        self._active_item = RectangleItem(
            QRectF(pos, pos), QColor("#7E9CD8"), 2, 0
        )
        self._active_item.setZValue(1)
        self._active_item.setOpacity(0.5)
        self.scene.addItem(self._active_item)

    def mouse_move(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            self._active_item.setRect(QRectF(self._start, pos).normalized())

    def mouse_release(self, event: QMouseEvent, pos: QPointF) -> None:
        if self._active_item is not None:
            rect = self._active_item.rect()
            self.scene.removeItem(self._active_item)
            self._active_item = None
            zoomed = self._zoom_region(rect)
            if zoomed is not None and not zoomed.isNull():
                src_c = QPointF(rect.center().x(), rect.center().y())
                src_r = max(rect.width(), rect.height()) / 2 * 1.1
                zoom = max(1.5, self.props.zoom_level)
                dest_r = src_r * zoom
                scene_rect = self.scene.sceneRect()
                dest_c = self._find_dest_position(src_c, src_r, dest_r, scene_rect)
                item = MagnifierCalloutItem(
                    src_c, src_r, dest_c, dest_r, zoomed,
                    zoom_level=self.props.zoom_level,
                    line_color=self.props.color,
                    line_width=self.props.stroke_width,
                )
                self.scene.addItem(item)
                self._push_add(item)
                self.scene._expand_scene_if_needed()

    def _zoom_region(self, rect: QRectF) -> QPixmap | None:
        try:
            w = max(1, int(rect.width()))
            h = max(1, int(rect.height()))
            zoom = max(1.5, self.props.zoom_level)

            scene_pixmap = QPixmap(w, h)
            scene_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(scene_pixmap)
            self.scene.render(painter, QRectF(0, 0, w, h), rect)
            painter.end()

            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            scene_pixmap.save(buf, "PNG")
            buf.close()

            pil_img = Image.open(BytesIO(bytes(ba)))
            out_w = max(1, int(w * zoom))
            out_h = max(1, int(h * zoom))
            pil_img = pil_img.resize((out_w, out_h), Image.Resampling.LANCZOS)

            out_buf = BytesIO()
            pil_img.save(out_buf, format="PNG")
            result = QPixmap()
            result.loadFromData(QByteArray(out_buf.getvalue()))
            return result
        except (OSError, UnidentifiedImageError, ValueError):
            logging.exception("MagnifierTool._zoom_region failed")
            return None

    def _find_dest_position(self, src_c: QPointF, src_r: float, dest_r: float, scene_rect: QRectF) -> QPointF:
        candidates = [
            QPointF(src_c.x() + src_r + dest_r + 20, src_c.y()),  # right
            QPointF(src_c.x() - src_r - dest_r - 20, src_c.y()),  # left
            QPointF(src_c.x(), src_c.y() - src_r - dest_r - 20),  # top
            QPointF(src_c.x(), src_c.y() + src_r + dest_r + 20),  # bottom
        ]
        for c in candidates:
            dx = c.x() - src_c.x()
            dy = c.y() - src_c.y()
            dist = math.hypot(dx, dy)
            if dist >= src_r + dest_r + 10:
                return c
        return candidates[0]
