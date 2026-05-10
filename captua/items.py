"""Custom QGraphicsItem subclasses for annotations."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFocusEvent,
    QFont,
    QFontDatabase,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtCore import QObject, QTimer

_EMOJI_FONT_FAMILY: str | None = None


def _emoji_font_family() -> str:
    global _EMOJI_FONT_FAMILY
    if _EMOJI_FONT_FAMILY is None:
        families = QFontDatabase.families()
        for name in ("Noto Color Emoji", "Segoe UI Emoji", "Apple Color Emoji"):
            if name in families:
                _EMOJI_FONT_FAMILY = name
                break
        else:
            _EMOJI_FONT_FAMILY = ""
    return _EMOJI_FONT_FAMILY
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
)


def _create_pen(color: QColor, width: float, cosmetic: bool = True) -> QPen:
    pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    pen.setCosmetic(cosmetic)
    return pen


class RectangleItem(QGraphicsRectItem):
    """Rectangle with optional rounded corners."""

    def __init__(self, rect: QRectF, color: QColor, width: float, radius: float = 0, fill_color: QColor | None = None, fill_alpha: int = 0, parent=None) -> None:
        super().__init__(rect, parent)
        self._radius = radius
        self._line_color = QColor(color)
        self._line_width = width
        self._fill_color = QColor(fill_color) if fill_color is not None else QColor("#FF5D62")
        self._fill_alpha = fill_alpha
        self.setPen(_create_pen(color, width))
        if fill_alpha > 0:
            fc = QColor(self._fill_color)
            fc.setAlpha(fill_alpha)
            self.setBrush(fc)
        else:
            self.setBrush(Qt.BrushStyle.NoBrush)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )

    def set_line_color(self, color: QColor) -> None:
        self._line_color = QColor(color)
        self.setPen(_create_pen(color, self._line_width))

    def line_color(self) -> QColor:
        return self._line_color

    def set_line_width(self, width: float) -> None:
        self._line_width = width
        self.setPen(_create_pen(self._line_color, width))

    def line_width(self) -> float:
        return self._line_width

    def set_fill_color(self, color: QColor) -> None:
        self._fill_color = QColor(color)
        if self._fill_alpha > 0:
            fc = QColor(color)
            fc.setAlpha(self._fill_alpha)
            self.setBrush(fc)

    def fill_color(self) -> QColor:
        return self._fill_color

    def set_fill_alpha(self, alpha: int) -> None:
        self._fill_alpha = alpha
        if alpha > 0:
            fc = QColor(self._fill_color)
            fc.setAlpha(alpha)
            self.setBrush(fc)
        else:
            self.setBrush(Qt.BrushStyle.NoBrush)

    def fill_alpha(self) -> int:
        return self._fill_alpha

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        if self._radius > 0:
            painter.drawRoundedRect(self.rect(), self._radius, self._radius)
        else:
            painter.drawRect(self.rect())
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawRect(self.rect().adjusted(-2, -2, 2, 2))


class EllipseItem(QGraphicsEllipseItem):
    """Circle or ellipse."""

    def __init__(self, rect: QRectF, color: QColor, width: float, fill_color: QColor | None = None, fill_alpha: int = 0, parent=None) -> None:
        super().__init__(rect, parent)
        self._line_color = QColor(color)
        self._line_width = width
        self._fill_color = QColor(fill_color) if fill_color is not None else QColor("#FF5D62")
        self._fill_alpha = fill_alpha
        self.setPen(_create_pen(color, width))
        if fill_alpha > 0:
            fc = QColor(self._fill_color)
            fc.setAlpha(fill_alpha)
            self.setBrush(fc)
        else:
            self.setBrush(Qt.BrushStyle.NoBrush)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )

    def set_line_color(self, color: QColor) -> None:
        self._line_color = QColor(color)
        self.setPen(_create_pen(color, self._line_width))

    def line_color(self) -> QColor:
        return self._line_color

    def set_line_width(self, width: float) -> None:
        self._line_width = width
        self.setPen(_create_pen(self._line_color, width))

    def line_width(self) -> float:
        return self._line_width

    def set_fill_color(self, color: QColor) -> None:
        self._fill_color = QColor(color)
        if self._fill_alpha > 0:
            fc = QColor(color)
            fc.setAlpha(self._fill_alpha)
            self.setBrush(fc)

    def fill_color(self) -> QColor:
        return self._fill_color

    def set_fill_alpha(self, alpha: int) -> None:
        self._fill_alpha = alpha
        if alpha > 0:
            fc = QColor(self._fill_color)
            fc.setAlpha(alpha)
            self.setBrush(fc)
        else:
            self.setBrush(Qt.BrushStyle.NoBrush)

    def fill_alpha(self) -> int:
        return self._fill_alpha

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.rect())
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawRect(self.rect().adjusted(-2, -2, 2, 2))


class LineItem(QGraphicsLineItem):
    """Simple line."""

    def __init__(self, p1: QPointF, p2: QPointF, color: QColor, width: float, parent=None) -> None:
        super().__init__(p1.x(), p1.y(), p2.x(), p2.y(), parent)
        self._line_color = QColor(color)
        self._line_width = width
        self.setPen(_create_pen(color, width))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )

    def set_line_color(self, color: QColor) -> None:
        self._line_color = QColor(color)
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)

    def line_color(self) -> QColor:
        return self._line_color

    def set_line_width(self, width: float) -> None:
        self._line_width = width
        pen = self.pen()
        pen.setWidthF(width)
        self.setPen(pen)

    def line_width(self) -> float:
        return self._line_width

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(self.pen())
        painter.drawLine(self.line())
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(self.line().p1(), 4, 4)
            painter.drawEllipse(self.line().p2(), 4, 4)


class ArrowItem(QGraphicsItem):
    """Line with an arrowhead at the end."""

    def __init__(self, p1: QPointF, p2: QPointF, color: QColor, width: float, parent=None) -> None:
        super().__init__(parent)
        self._p1 = QPointF(p1)
        self._p2 = QPointF(p2)
        self._color = color
        self._width = width
        self._head_len = max(15, width * 3)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(1)

    def set_end(self, p2: QPointF) -> None:
        self.prepareGeometryChange()
        self._p2 = QPointF(p2)
        self.update()

    def set_line_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.update()

    def line_color(self) -> QColor:
        return self._color

    def set_line_width(self, width: float) -> None:
        self.prepareGeometryChange()
        self._width = width
        self._head_len = max(15, width * 3)
        self.update()

    def line_width(self) -> float:
        return self._width

    def boundingRect(self) -> QRectF:
        x1, y1 = self._p1.x(), self._p1.y()
        x2, y2 = self._p2.x(), self._p2.y()
        pad = self._head_len + self._width + 4
        return QRectF(
            min(x1, x2) - pad,
            min(y1, y2) - pad,
            abs(x2 - x1) + pad * 2,
            abs(y2 - y1) + pad * 2,
        )

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(_create_pen(self._color, self._width))
        painter.setBrush(self._color)
        painter.drawLine(self._p1, self._p2)

        # Arrowhead
        angle = math.atan2(self._p2.y() - self._p1.y(), self._p2.x() - self._p1.x())
        head_angle = math.pi / 6  # 30 degrees

        p3 = QPointF(
            self._p2.x() - self._head_len * math.cos(angle - head_angle),
            self._p2.y() - self._head_len * math.sin(angle - head_angle),
        )
        p4 = QPointF(
            self._p2.x() - self._head_len * math.cos(angle + head_angle),
            self._p2.y() - self._head_len * math.sin(angle + head_angle),
        )

        arrow = QPolygonF([self._p2, p3, p4])
        painter.drawPolygon(arrow)

        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(self._p1, 4, 4)
            painter.drawEllipse(self._p2, 4, 4)


class PenItem(QGraphicsItem):
    """Freehand pen stroke drawn as connected line segments."""

    def __init__(self, color: QColor, width: float, parent=None) -> None:
        super().__init__(parent)
        self._points: list[QPointF] = []
        self._color = color
        self._width = width
        self._raw_bbox = QRectF()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(1)

    def add_point(self, point: QPointF) -> None:
        self.prepareGeometryChange()
        self._points.append(QPointF(point))
        self._raw_bbox = self._raw_bbox.united(QRectF(point.x(), point.y(), 0, 0))
        self.update()

    def set_line_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.update()

    def line_color(self) -> QColor:
        return self._color

    def set_line_width(self, width: float) -> None:
        self.prepareGeometryChange()
        self._width = width
        self.update()

    def line_width(self) -> float:
        return self._width

    def boundingRect(self) -> QRectF:
        if self._raw_bbox.isNull():
            return QRectF(0, 0, 1, 1)
        pad = self._width + 4
        return self._raw_bbox.adjusted(-pad, -pad, pad, pad)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if len(self._points) < 2:
            return
        painter.setPen(_create_pen(self._color, self._width))
        for i in range(len(self._points) - 1):
            painter.drawLine(self._points[i], self._points[i + 1])
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            for p in self._points:
                painter.drawEllipse(p, 3, 3)


class MarkerItem(QGraphicsItem):
    """Highlighter / marker stroke."""

    def __init__(self, fill_color: QColor, fill_alpha: int, width: float, parent=None) -> None:
        super().__init__(parent)
        self._points: list[QPointF] = []
        self._fill_base_color = QColor(fill_color)
        self._fill_alpha = fill_alpha
        self._fill_color = QColor(fill_color)
        self._fill_color.setAlpha(fill_alpha)
        self._width = width
        self._raw_bbox = QRectF()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(0.5)

    def add_point(self, point: QPointF) -> None:
        self.prepareGeometryChange()
        self._points.append(QPointF(point))
        self._raw_bbox = self._raw_bbox.united(QRectF(point.x(), point.y(), 0, 0))
        self.update()

    def set_fill_color(self, color: QColor) -> None:
        self._fill_base_color = QColor(color)
        self._fill_color = QColor(color)
        self._fill_color.setAlpha(self._fill_alpha)
        self.update()

    def fill_color(self) -> QColor:
        return self._fill_base_color

    def set_fill_alpha(self, alpha: int) -> None:
        self._fill_alpha = alpha
        self._fill_color.setAlpha(alpha)
        self.update()

    def fill_alpha(self) -> int:
        return self._fill_alpha

    def boundingRect(self) -> QRectF:
        if self._raw_bbox.isNull():
            return QRectF(0, 0, 1, 1)
        pad = self._width + 4
        return self._raw_bbox.adjusted(-pad, -pad, pad, pad)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if len(self._points) < 2:
            return
        path = QPainterPath()
        path.moveTo(self._points[0])
        for p in self._points[1:]:
            path.lineTo(p)

        stroker = QPainterPathStroker()
        stroker.setWidth(self._width)
        stroker.setCapStyle(Qt.PenCapStyle.SquareCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        stroke_path = stroker.createStroke(path)

        painter.fillPath(stroke_path, self._fill_color)

        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            for p in self._points:
                painter.drawEllipse(p, 3, 3)


class TextItem(QGraphicsTextItem):
    """Editable on-canvas text."""

    def __init__(self, pos: QPointF, color: QColor, parent=None) -> None:
        super().__init__(parent)
        self.setDefaultTextColor(color)
        self.setFont(QFont("Inter", 16))
        self.setPlainText("")
        self.setPos(pos)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setZValue(1)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

    def set_line_color(self, color: QColor) -> None:
        self.setDefaultTextColor(color)

    def line_color(self) -> QColor:
        return self.defaultTextColor()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        if self.isSelected() or (self.hasFocus() and self.toPlainText() == ""):
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawRect(self.boundingRect().adjusted(-2, -2, 2, 2))

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        scene = self.scene()
        if scene is not None and hasattr(scene, "_expand_scene_if_needed"):
            scene._expand_scene_if_needed()


class LabelItem(QGraphicsTextItem):
    """Text in a rounded box with background."""

    def __init__(self, pos: QPointF, color: QColor, parent=None) -> None:
        super().__init__(parent)
        self.setDefaultTextColor(QColor("#DCD7BA"))
        self.setFont(QFont("Inter", 14))
        self.setPlainText("Label")
        self.setPos(pos)
        self._bg_color = QColor("#1F1F28")
        self._border_color = color
        self._border_width = 2.0
        self._radius = 8.0
        self._padding = 8
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setZValue(1)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

    def set_border_color(self, color: QColor) -> None:
        self._border_color = color
        self.update()

    def set_line_color(self, color: QColor) -> None:
        self._border_color = QColor(color)
        self.update()

    def line_color(self) -> QColor:
        return self._border_color

    def set_line_width(self, width: float) -> None:
        self._border_width = width
        self.update()

    def line_width(self) -> float:
        return self._border_width

    def paint(self, painter: QPainter, option, widget=None) -> None:
        # Draw background rounded rect based on text bounding rect
        text_rect = super().boundingRect()
        pad = self._padding
        bg_rect = text_rect.adjusted(-pad, -pad, pad, pad)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._bg_color)
        painter.drawRoundedRect(bg_rect, self._radius, self._radius)

        painter.setPen(QPen(self._border_color, self._border_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bg_rect, self._radius, self._radius)

        # Draw text
        super().paint(painter, option, widget)

        if self.isSelected() or (self.hasFocus() and self.toPlainText() == ""):
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(bg_rect.adjusted(-2, -2, 2, 2), self._radius, self._radius)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        scene = self.scene()
        if scene is not None and hasattr(scene, "_expand_scene_if_needed"):
            scene._expand_scene_if_needed()

    def boundingRect(self) -> QRectF:
        r = super().boundingRect()
        pad = self._padding + 4
        return r.adjusted(-pad, -pad, pad, pad)


class CounterItem(QGraphicsItem):
    """Numbered bubble (auto-incrementing counter)."""

    def __init__(self, pos: QPointF, number: int, color: QColor, parent=None) -> None:
        super().__init__(parent)
        self._number = number
        self._color = color
        self._radius = 16
        self.setPos(pos)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(1)

    def set_line_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.update()

    def line_color(self) -> QColor:
        return self._color

    def boundingRect(self) -> QRectF:
        r = self._radius + 2
        return QRectF(-r, -r, r * 2, r * 2)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(QPointF(0, 0), self._radius, self._radius)
        painter.setPen(QPen(QColor("#DCD7BA"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        font = QFont("Inter", 12)
        font.setBold(True)
        painter.setFont(font)
        text = str(self._number)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        th = fm.height()
        painter.drawText(int(-tw / 2), int(th / 2 - fm.descent()), text)
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(QPointF(0, 0), self._radius + 2, self._radius + 2)


class RulerItem(QGraphicsItem):
    """Line that displays pixel distance."""

    def __init__(self, p1: QPointF, p2: QPointF, color: QColor, width: float, parent=None) -> None:
        super().__init__(parent)
        self._p1 = QPointF(p1)
        self._p2 = QPointF(p2)
        self._color = color
        self._width = width
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(1)

    def set_end(self, p2: QPointF) -> None:
        self.prepareGeometryChange()
        self._p2 = QPointF(p2)
        self.update()

    def set_line_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.update()

    def line_color(self) -> QColor:
        return self._color

    def set_line_width(self, width: float) -> None:
        self.prepareGeometryChange()
        self._width = width
        self.update()

    def line_width(self) -> float:
        return self._width

    def _distance(self) -> float:
        dx = self._p2.x() - self._p1.x()
        dy = self._p2.y() - self._p1.y()
        return math.hypot(dx, dy)

    def boundingRect(self) -> QRectF:
        x1, y1 = self._p1.x(), self._p1.y()
        x2, y2 = self._p2.x(), self._p2.y()
        pad = 30
        return QRectF(
            min(x1, x2) - pad,
            min(y1, y2) - pad,
            abs(x2 - x1) + pad * 2,
            abs(y2 - y1) + pad * 2,
        )

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(_create_pen(self._color, self._width))
        painter.drawLine(self._p1, self._p2)

        # Distance text at midpoint
        mid = QPointF((self._p1.x() + self._p2.x()) / 2, (self._p1.y() + self._p2.y()) / 2)
        dist = self._distance()
        text = f"{dist:.1f}px"
        font = QFont("Inter", 11)
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        th = fm.height()

        # Text background
        pad = 4
        bg = QRectF(mid.x() - tw / 2 - pad, mid.y() - th / 2 - pad, tw + pad * 2, th + pad * 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1F1F28"))
        painter.drawRoundedRect(bg, 4, 4)

        painter.setPen(QPen(QColor("#DCD7BA"), 1))
        painter.drawText(int(mid.x() - tw / 2), int(mid.y() + th / 2 - fm.descent()), text)

        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(self._p1, 4, 4)
            painter.drawEllipse(self._p2, 4, 4)


class SpotlightItem(QGraphicsItem):
    """Dark overlay with a transparent focus rectangle."""

    def __init__(self, overlay_rect: QRectF, spotlight_rect: QRectF, fill_color: QColor | None = None, fill_alpha: int = 180, parent=None) -> None:
        super().__init__(parent)
        self._overlay = overlay_rect
        self._spotlight = spotlight_rect
        c = QColor(fill_color) if fill_color is not None else QColor(0, 0, 0)
        self._fill_base_color = QColor(c)
        self._fill_alpha = fill_alpha
        c.setAlpha(fill_alpha)
        self._fill = c
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(0.8)

    def set_spotlight(self, rect: QRectF) -> None:
        self.prepareGeometryChange()
        self._spotlight = rect
        self.update()

    def set_fill_color(self, color: QColor) -> None:
        self._fill_base_color = QColor(color)
        self._fill = QColor(color)
        self._fill.setAlpha(self._fill_alpha)
        self.update()

    def fill_color(self) -> QColor:
        return self._fill_base_color

    def set_fill_alpha(self, alpha: int) -> None:
        self._fill_alpha = alpha
        self._fill.setAlpha(alpha)
        self.update()

    def fill_alpha(self) -> int:
        return self._fill_alpha

    def boundingRect(self) -> QRectF:
        return self._overlay

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._fill)
        ox, oy, ow, oh = self._overlay.x(), self._overlay.y(), self._overlay.width(), self._overlay.height()
        sx, sy, sw, sh = self._spotlight.x(), self._spotlight.y(), self._spotlight.width(), self._spotlight.height()
        # Top
        painter.drawRect(ox, oy, ow, sy - oy)
        # Bottom
        painter.drawRect(ox, sy + sh, ow, oy + oh - (sy + sh))
        # Left
        painter.drawRect(ox, sy, sx - ox, sh)
        # Right
        painter.drawRect(sx + sw, sy, ox + ow - (sx + sw), sh)
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawRect(self._spotlight.adjusted(-2, -2, 2, 2))


class BlurItem(QGraphicsItem):
    """Blurred region of the base image with soft edges."""

    def __init__(self, rect: QRectF, blurred_pixmap: QPixmap, offset: QPointF, pad: int, parent=None) -> None:
        super().__init__(parent)
        self._rect = rect
        self._pixmap = blurred_pixmap
        self._offset = offset
        self._pad = pad
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(0.9)

    def boundingRect(self) -> QRectF:
        return self._rect.adjusted(-self._pad, -self._pad, self._pad, self._pad)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.drawPixmap(self._rect.topLeft() + self._offset, self._pixmap)
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawRect(self._rect.adjusted(-2, -2, 2, 2))


class _MagnifierPosWatcher(QObject):
    """Polls the magnifier's position and re-captures the zoomed region when it moves.

    PySide6 does not call itemChange() for ItemPositionHasChanged, so we use a
    short timer (~30 ms) to detect position changes and update the pixmap live.
    """

    def __init__(self, item: "MagnifierCalloutItem") -> None:
        super().__init__()
        self._item = item
        self._last_pos = item.pos()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._timer.start(30)
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._item._update_pixmap)

    def _check(self) -> None:
        item = self._item
        if item.scene() is None:
            self._timer.stop()
            self._render_timer.stop()
            return
        current = item.pos()
        if current != self._last_pos:
            self._last_pos = current
            self._render_timer.start(80)


class MagnifierCalloutItem(QGraphicsItem):
    """Circular magnifier callout: source circle → line → dest circle with zoomed image.

    The item's position is anchored at the source center.  The destination is stored
    as a local offset so the whole callout moves together when dragged.  The zoomed
    pixmap is re-captured from the new source region after the item stops moving.
    """

    def __init__(self, src_center: QPointF, src_radius: float, dest_center: QPointF, dest_radius: float, zoomed_pixmap: QPixmap, zoom_level: float = 2.0, line_color: QColor | None = None, line_width: float = 2.0, parent=None) -> None:
        super().__init__(parent)
        # Position the item at the source center; everything else is local
        self.setPos(src_center)
        self._src_c = QPointF(0, 0)
        self._src_r = src_radius
        self._dest_c = dest_center - src_center
        self._dest_r = dest_radius
        self._pixmap = zoomed_pixmap
        self._zoom_level = zoom_level
        self._line_color = QColor(line_color) if line_color is not None else QColor("#7E9CD8")
        self._line_width = line_width
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(1)
        # PySide6 itemChange doesn't fire for position changes, so we poll
        self._pos_watcher = _MagnifierPosWatcher(self)

    def set_line_color(self, color: QColor) -> None:
        self._line_color = QColor(color)
        self.update()

    def line_color(self) -> QColor:
        return self._line_color

    def set_line_width(self, width: float) -> None:
        self._line_width = width
        self.update()

    def line_width(self) -> float:
        return self._line_width

    def zoom_level(self) -> float:
        return self._zoom_level

    def set_zoom_level(self, zoom: float) -> None:
        zoom = max(1.5, zoom)
        if abs(self._zoom_level - zoom) < 0.01:
            return
        self.prepareGeometryChange()
        self._zoom_level = zoom
        self._dest_r = self._src_r * zoom
        self._update_pixmap()

    def boundingRect(self) -> QRectF:
        x1 = min(self._src_c.x() - self._src_r, self._dest_c.x() - self._dest_r)
        y1 = min(self._src_c.y() - self._src_r, self._dest_c.y() - self._dest_r)
        x2 = max(self._src_c.x() + self._src_r, self._dest_c.x() + self._dest_r)
        y2 = max(self._src_c.y() + self._src_r, self._dest_c.y() + self._dest_r)
        return QRectF(x1, y1, x2 - x1, y2 - y1).adjusted(-4, -4, 4, 4)

    def _update_pixmap(self) -> None:
        scene = self.scene()
        if scene is None:
            return
        # Skip rendering ourselves into the captured pixmap
        self._updating_pixmap = True
        try:
            src_scene = self.scenePos() + self._src_c
            r = self._src_r
            rect = QRectF(src_scene.x() - r, src_scene.y() - r, r * 2, r * 2)
            w = max(1, int(rect.width()))
            h = max(1, int(rect.height()))
            pixmap = QPixmap(w, h)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            scene.render(painter, QRectF(0, 0, w, h), rect)
            painter.end()
            zoom = max(1.5, self._zoom_level)
            out_w = max(1, int(w * zoom))
            out_h = max(1, int(h * zoom))
            self._pixmap = pixmap.scaled(out_w, out_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        finally:
            self._updating_pixmap = False
        self.update()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if getattr(self, "_updating_pixmap", False):
            return
        # Connecting line between circle edges
        dx = self._dest_c.x() - self._src_c.x()
        dy = self._dest_c.y() - self._src_c.y()
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            nx = dx / dist
            ny = dy / dist
            p1 = QPointF(self._src_c.x() + nx * self._src_r, self._src_c.y() + ny * self._src_r)
            p2 = QPointF(self._dest_c.x() - nx * self._dest_r, self._dest_c.y() - ny * self._dest_r)
            pen = _create_pen(self._line_color, self._line_width)
            painter.setPen(pen)
            painter.drawLine(p1, p2)

        # Source circle outline
        painter.setPen(_create_pen(self._line_color, self._line_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self._src_c, self._src_r, self._src_r)

        # Dest circle with zoomed image
        clip = QPainterPath()
        clip.addEllipse(self._dest_c, self._dest_r, self._dest_r)
        painter.setClipPath(clip)
        px = int(self._dest_c.x() - self._pixmap.width() / 2)
        py = int(self._dest_c.y() - self._pixmap.height() / 2)
        painter.drawPixmap(px, py, self._pixmap)
        painter.setClipping(False)

        # Dest circle border
        painter.setPen(_create_pen(self._line_color, self._line_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self._dest_c, self._dest_r, self._dest_r)

        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(self._src_c, self._src_r + 2, self._src_r + 2)
            painter.drawEllipse(self._dest_c, self._dest_r + 2, self._dest_r + 2)


class ShapeItem(QGraphicsItem):
    """Geometric shape drawn as outline or filled."""

    SHAPE_NAMES = {
        "heart": "Heart",
        "star5": "Star",
        "star4": "4-Point Star",
        "triangle": "Triangle",
        "diamond": "Diamond",
        "hexagon": "Hexagon",
        "arrow_shape": "Arrow",
        "cross": "Cross",
        "moon": "Moon",
    }

    def __init__(self, rect: QRectF, shape_type: str, color: QColor, width: float, fill_color: QColor | None = None, fill_alpha: int = 0, filled: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._rect = QRectF(rect)
        self._shape_type = shape_type
        self._color = color
        self._width = width
        self._fill_color = QColor(fill_color) if fill_color is not None else QColor(color)
        self._fill_alpha = fill_alpha
        self._filled = filled
        self._cached_path: QPainterPath | None = None
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(1)

    def setRect(self, rect: QRectF) -> None:
        self.prepareGeometryChange()
        self._rect = QRectF(rect)
        self._cached_path = None
        self.update()

    def rect(self) -> QRectF:
        return self._rect

    def set_line_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.update()

    def line_color(self) -> QColor:
        return self._color

    def set_line_width(self, width: float) -> None:
        self.prepareGeometryChange()
        self._width = width
        self.update()

    def line_width(self) -> float:
        return self._width

    def set_fill_color(self, color: QColor) -> None:
        self._fill_color = QColor(color)
        self.update()

    def fill_color(self) -> QColor:
        return self._fill_color

    def set_fill_alpha(self, alpha: int) -> None:
        self._fill_alpha = alpha
        self.update()

    def fill_alpha(self) -> int:
        return self._fill_alpha

    def boundingRect(self) -> QRectF:
        pad = self._width + 4
        return self._rect.adjusted(-pad, -pad, pad, pad)

    def _build_path(self) -> QPainterPath:
        path = QPainterPath()
        r = self._rect
        cx = r.center().x()
        cy = r.center().y()
        w = r.width()
        h = r.height()

        if self._shape_type == "heart":
            # Normalized heart in [-1, 1] then scale
            s = min(w, h) * 0.5
            path.moveTo(cx, cy + s * 0.6)
            path.cubicTo(cx - s * 0.1, cy + s * 0.3, cx - s * 0.5, cy + s * 0.2, cx - s * 0.5, cy - s * 0.1)
            path.cubicTo(cx - s * 0.5, cy - s * 0.4, cx - s * 0.25, cy - s * 0.5, cx, cy - s * 0.3)
            path.cubicTo(cx + s * 0.25, cy - s * 0.5, cx + s * 0.5, cy - s * 0.4, cx + s * 0.5, cy - s * 0.1)
            path.cubicTo(cx + s * 0.5, cy + s * 0.2, cx + s * 0.1, cy + s * 0.3, cx, cy + s * 0.6)
            path.closeSubpath()

        elif self._shape_type == "star5":
            outer = min(w, h) * 0.5
            inner = outer * 0.4
            pts = []
            for i in range(10):
                angle = math.pi / 2 + i * math.pi / 5
                radius = outer if i % 2 == 0 else inner
                pts.append(QPointF(cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
            path.moveTo(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
            path.closeSubpath()

        elif self._shape_type == "star4":
            outer = min(w, h) * 0.5
            inner = outer * 0.35
            pts = []
            for i in range(8):
                angle = math.pi / 2 + i * math.pi / 4
                radius = outer if i % 2 == 0 else inner
                pts.append(QPointF(cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
            path.moveTo(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
            path.closeSubpath()

        elif self._shape_type == "triangle":
            s = min(w, h) * 0.5
            path.moveTo(cx, cy - s)
            path.lineTo(cx - s * 0.866, cy + s * 0.5)
            path.lineTo(cx + s * 0.866, cy + s * 0.5)
            path.closeSubpath()

        elif self._shape_type == "diamond":
            path.moveTo(cx, cy - h * 0.5)
            path.lineTo(cx + w * 0.5, cy)
            path.lineTo(cx, cy + h * 0.5)
            path.lineTo(cx - w * 0.5, cy)
            path.closeSubpath()

        elif self._shape_type == "hexagon":
            s = min(w, h) * 0.5
            pts = []
            for i in range(6):
                angle = math.pi / 2 + i * math.pi / 3
                pts.append(QPointF(cx + s * math.cos(angle), cy - s * math.sin(angle)))
            path.moveTo(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
            path.closeSubpath()

        elif self._shape_type == "arrow_shape":
            # Arrow pointing right, scaled to rect
            aw = w * 0.5
            ah = h * 0.35
            path.moveTo(cx - aw, cy - ah)
            path.lineTo(cx, cy - ah)
            path.lineTo(cx, cy - h * 0.5)
            path.lineTo(cx + aw, cy)
            path.lineTo(cx, cy + h * 0.5)
            path.lineTo(cx, cy + ah)
            path.lineTo(cx - aw, cy + ah)
            path.closeSubpath()

        elif self._shape_type == "cross":
            t = min(w, h) * 0.15
            hw = w * 0.5
            hh = h * 0.5
            path.moveTo(cx - t, cy - hh)
            path.lineTo(cx + t, cy - hh)
            path.lineTo(cx + t, cy - t)
            path.lineTo(cx + hw, cy - t)
            path.lineTo(cx + hw, cy + t)
            path.lineTo(cx + t, cy + t)
            path.lineTo(cx + t, cy + hh)
            path.lineTo(cx - t, cy + hh)
            path.lineTo(cx - t, cy + t)
            path.lineTo(cx - hw, cy + t)
            path.lineTo(cx - hw, cy - t)
            path.lineTo(cx - t, cy - t)
            path.closeSubpath()

        elif self._shape_type == "moon":
            s = min(w, h) * 0.5
            path.addEllipse(QPointF(cx - s * 0.15, cy), s, s)
            inner = QPainterPath()
            inner.addEllipse(QPointF(cx + s * 0.25, cy), s * 0.85, s * 0.85)
            path = path.subtracted(inner)

        else:
            # Fallback: rectangle
            path.addRect(r)

        return path

    def paint(self, painter: QPainter, option, widget=None) -> None:
        pen = _create_pen(self._color, self._width)
        painter.setPen(pen)
        if self._filled:
            fill = QColor(self._fill_color)
            fill.setAlpha(self._fill_alpha)
            painter.setBrush(fill)
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        if self._cached_path is None:
            self._cached_path = self._build_path()
        painter.drawPath(self._cached_path)
        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self._rect.adjusted(-2, -2, 2, 2))


class EmojiItem(QGraphicsItem):
    """Emoji placed on canvas, resizable by dragging."""

    def __init__(self, rect: QRectF, emoji: str, parent=None) -> None:
        super().__init__(parent)
        self._rect = QRectF(rect)
        self._emoji = emoji
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.setZValue(1)

    def setRect(self, rect: QRectF) -> None:
        self.prepareGeometryChange()
        self._rect = QRectF(rect)
        self.update()

    def rect(self) -> QRectF:
        return self._rect

    def emoji(self) -> str:
        return self._emoji

    def boundingRect(self) -> QRectF:
        # Emoji font metrics often exceed the rect size, so we add generous padding
        # proportional to the font size to prevent clipping during drag.
        size = max(int(min(self._rect.width(), self._rect.height())), 12)
        pad = max(size // 4, 8)
        return self._rect.adjusted(-pad, -pad, pad, pad)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        size = max(int(min(self._rect.width(), self._rect.height())), 12)
        font = QFont(_emoji_font_family(), size)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(self._emoji)
        th = fm.height()
        x = int(self._rect.center().x() - tw / 2)
        y = int(self._rect.center().y() + th / 2 - fm.descent())
        painter.drawText(x, y, self._emoji)

        if self.isSelected():
            painter.setPen(QPen(QColor("#7E9CD8"), 1, Qt.PenStyle.DashLine))
            painter.drawRect(self._rect.adjusted(-2, -2, 2, 2))


class CanvasImageItem(QGraphicsPixmapItem):
    """Pixmap item with optional rounded corners."""

    def __init__(self, pixmap: QPixmap, corner_radius: float = 0, parent=None) -> None:
        super().__init__(pixmap, parent)
        self._corner_radius = corner_radius
        # Images are not movable — only annotations should expand the backdrop
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def set_corner_radius(self, radius: float) -> None:
        self._corner_radius = radius
        self.update()

    def corner_radius(self) -> float:
        return self._corner_radius

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if self._corner_radius > 0:
            path = QPainterPath()
            path.addRoundedRect(self.boundingRect(), self._corner_radius, self._corner_radius)
            painter.setClipPath(path)
        super().paint(painter, option, widget)


class CropOverlayItem(QGraphicsItem):
    """Dark overlay with a clear rectangle showing the crop selection."""

    def __init__(self, overlay_rect: QRectF, crop_rect: QRectF, parent=None) -> None:
        super().__init__(parent)
        self._overlay = overlay_rect
        self._crop = crop_rect
        self.setZValue(2)

    @property
    def crop_rect(self) -> QRectF:
        return QRectF(self._crop)

    def set_crop(self, rect: QRectF) -> None:
        self.prepareGeometryChange()
        self._crop = rect
        self.update()

    def boundingRect(self) -> QRectF:
        return self._overlay

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 140))
        ox, oy, ow, oh = self._overlay.x(), self._overlay.y(), self._overlay.width(), self._overlay.height()
        cx, cy, cw, ch = self._crop.x(), self._crop.y(), self._crop.width(), self._crop.height()
        # Top
        painter.drawRect(ox, oy, ow, cy - oy)
        # Bottom
        painter.drawRect(ox, cy + ch, ow, oy + oh - (cy + ch))
        # Left
        painter.drawRect(ox, cy, cx - ox, ch)
        # Right
        painter.drawRect(cx + cw, cy, ox + ow - (cx + cw), ch)

        # Border around crop
        painter.setPen(QPen(QColor("#7E9CD8"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._crop)
