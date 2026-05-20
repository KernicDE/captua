"""Toolbar icons drawn programmatically as crisp monochrome pixmaps."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

_ICON_SIZE = 20
_STROKE = 1.5
_COLOR = QColor("#DCD7BA")
_COLOR_ACTIVE = QColor("#F4F4F5")


def _create_pixmap() -> QPixmap:
    pm = QPixmap(_ICON_SIZE, _ICON_SIZE)
    pm.fill(Qt.GlobalColor.transparent)
    return pm


def _painter(pm: QPixmap) -> QPainter:
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(_COLOR, _STROKE, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    return p


def _finish(p: QPainter) -> QPixmap:
    p.end()
    return p.device()


def icon(name: str, active: bool = False) -> QPixmap:
    """Return a 20×20 pixmap for the given tool/action name."""
    pm = _create_pixmap()
    p = _painter(pm)
    color = _COLOR_ACTIVE if active else _COLOR
    p.setPen(QPen(color, _STROKE, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    s = _ICON_SIZE
    hs = s / 2

    if name == "select":
        path = QPainterPath()
        path.moveTo(4, 3)
        path.lineTo(4, 16)
        path.lineTo(7, 12)
        path.lineTo(10, 18)
        path.lineTo(13, 17)
        path.lineTo(10, 11)
        path.lineTo(15, 11)
        path.closeSubpath()
        p.drawPath(path)

    elif name == "rectangle":
        p.drawRect(QRectF(3.5, 4.5, 13, 11))

    elif name == "ellipse":
        p.drawEllipse(QRectF(3.5, 4.5, 13, 11))

    elif name == "line":
        p.drawLine(QPointF(4, 16), QPointF(16, 4))

    elif name == "arrow":
        p.drawLine(QPointF(3, 11), QPointF(14, 11))
        p.drawLine(QPointF(10, 6), QPointF(15, 11))
        p.drawLine(QPointF(10, 16), QPointF(15, 11))

    elif name == "pen":
        p.drawLine(QPointF(14, 3), QPointF(5, 14))
        p.drawLine(QPointF(12, 15), QPointF(16, 17))
        p.drawLine(QPointF(5, 14), QPointF(3, 17))
        p.drawLine(QPointF(3, 17), QPointF(6, 16))

    elif name == "marker":
        p.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(4, 14), QPointF(14, 8))

    elif name == "shape":
        # Star / polygon
        pts = [
            QPointF(10, 2), QPointF(12, 7), QPointF(18, 7),
            QPointF(13, 11), QPointF(15, 17), QPointF(10, 13),
            QPointF(5, 17), QPointF(7, 11), QPointF(2, 7),
            QPointF(8, 7),
        ]
        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        p.drawPath(path)

    elif name == "emoji":
        p.drawEllipse(QRectF(3, 3, 14, 14))
        p.drawArc(QRectF(6, 6, 8, 8), 30 * 16, 120 * 16)
        p.drawPoint(QPointF(7.5, 9))
        p.drawPoint(QPointF(12.5, 9))

    elif name == "text":
        p.drawLine(QPointF(6, 5), QPointF(14, 5))
        p.drawLine(QPointF(10, 5), QPointF(10, 15))
        p.drawLine(QPointF(7, 15), QPointF(13, 15))

    elif name == "label":
        p.drawLine(QPointF(3, 6), QPointF(14, 6))
        p.drawLine(QPointF(14, 6), QPointF(17, 10))
        p.drawLine(QPointF(17, 10), QPointF(14, 14))
        p.drawLine(QPointF(14, 14), QPointF(3, 14))
        p.drawLine(QPointF(3, 14), QPointF(3, 6))
        p.drawLine(QPointF(6, 10), QPointF(11, 10))

    elif name == "counter":
        p.drawEllipse(QRectF(3, 3, 14, 14))
        p.drawLine(QPointF(10, 7), QPointF(10, 13))
        p.drawLine(QPointF(7, 10), QPointF(13, 10))

    elif name == "ruler":
        p.drawLine(QPointF(3, 6), QPointF(17, 6))
        p.drawLine(QPointF(17, 6), QPointF(17, 14))
        p.drawLine(QPointF(17, 14), QPointF(3, 14))
        p.drawLine(QPointF(3, 14), QPointF(3, 6))
        for x in (5, 8, 11, 14):
            p.drawLine(QPointF(x, 6), QPointF(x, 9))

    elif name == "spotlight":
        p.drawLine(QPointF(10, 3), QPointF(10, 10))
        p.drawEllipse(QRectF(5, 10, 10, 6))
        p.drawArc(QRectF(7, 11, 6, 4), 0, -180 * 16)

    elif name == "blur":
        for i, r in enumerate([3, 5, 7, 9]):
            alpha = 180 - i * 40
            c = QColor(color)
            c.setAlpha(alpha)
            p.setPen(QPen(c, 1.2, Qt.PenStyle.SolidLine))
            p.drawEllipse(QRectF(10 - r, 10 - r, r * 2, r * 2))

    elif name == "magnifier":
        p.drawEllipse(QRectF(3, 3, 11, 11))
        p.drawLine(QPointF(12, 12), QPointF(17, 17))
        p.drawLine(QPointF(6, 7), QPointF(6, 10))
        p.drawLine(QPointF(11, 7), QPointF(11, 10))
        p.drawArc(QRectF(6, 8, 5, 4), 0, -180 * 16)

    elif name == "eyedropper":
        # Bulb at top
        p.drawEllipse(QRectF(11, 1, 7, 7))
        # Stem
        p.drawLine(QPointF(14, 7), QPointF(7, 15))
        # Tip
        path = QPainterPath()
        path.moveTo(7, 15)
        path.lineTo(5, 18)
        path.lineTo(9, 16)
        path.closeSubpath()
        p.drawPath(path)

    elif name == "close":
        p.drawLine(QPointF(5, 5), QPointF(15, 15))
        p.drawLine(QPointF(15, 5), QPointF(5, 15))

    elif name == "save":
        p.drawRect(QRectF(4, 3, 12, 14))
        p.drawLine(QPointF(7, 3), QPointF(7, 8))
        p.drawLine(QPointF(7, 8), QPointF(13, 8))
        p.drawLine(QPointF(13, 8), QPointF(13, 3))
        p.drawLine(QPointF(7, 12), QPointF(13, 12))

    elif name == "copy":
        p.drawRect(QRectF(6, 3, 10, 12))
        p.drawRect(QRectF(3, 6, 10, 12))

    elif name == "import":
        p.drawLine(QPointF(10, 3), QPointF(10, 14))
        p.drawLine(QPointF(6, 9), QPointF(10, 14))
        p.drawLine(QPointF(14, 9), QPointF(10, 14))
        p.drawLine(QPointF(4, 16), QPointF(16, 16))

    elif name == "capture":
        p.drawRect(QRectF(4, 4, 12, 10))
        p.drawEllipse(QRectF(8, 7, 4, 4))
        p.drawLine(QPointF(14, 4), QPointF(14, 6))

    elif name == "backdrop":
        p.drawRect(QRectF(3, 5, 14, 10))
        p.drawLine(QPointF(5, 7), QPointF(15, 7))
        p.drawLine(QPointF(5, 9), QPointF(13, 9))
        p.drawLine(QPointF(5, 11), QPointF(14, 11))

    elif name == "stroke":
        p.drawLine(QPointF(2, 10), QPointF(18, 10))

    elif name == "fill":
        p.setBrush(color)
        p.drawRect(QRectF(4, 4, 12, 12))

    else:
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, name[0].upper())

    return _finish(p)
