from PySide6.QtGui import QPainter, QPixmap, QColor, QPen, QIcon, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF, QSize

def get_vector_icon(icon_type: str, color_normal: str = "#8B949E", color_active: str = "#cba6f7", size: int = 24) -> QIcon:
    """Generate crisp, platform-independent vector QIcon objects for UI navigation."""
    def _draw_pixmap(color_hex: str) -> QPixmap:
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(color_hex), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        if icon_type == "attendance":  # Camera
            p.drawRoundedRect(QRectF(3, 7, 18, 13), 2.5, 2.5)
            path = QPainterPath()
            path.moveTo(8, 7)
            path.lineTo(9.5, 4.5)
            path.lineTo(14.5, 4.5)
            path.lineTo(16, 7)
            p.drawPath(path)
            p.drawEllipse(QPointF(12, 13.5), 3.5, 3.5)
        elif icon_type == "students":  # Users
            p.drawEllipse(QPointF(9, 8), 3, 3)
            path1 = QPainterPath()
            path1.arcMoveTo(QRectF(3, 13, 12, 8), 0)
            path1.arcTo(QRectF(3, 13, 12, 8), 0, 180)
            p.drawPath(path1)
            p.drawEllipse(QPointF(16, 9), 2.5, 2.5)
            path2 = QPainterPath()
            path2.arcMoveTo(QRectF(11, 14, 10, 7), 0)
            path2.arcTo(QRectF(11, 14, 10, 7), 0, 180)
            p.drawPath(path2)
        elif icon_type == "reports":  # Bar Chart
            p.drawLine(4, 20, 20, 20)
            p.drawLine(4, 4, 4, 20)
            p.fillRect(QRectF(7, 13, 2.5, 7), QColor(color_hex))
            p.fillRect(QRectF(11, 9, 2.5, 11), QColor(color_hex))
            p.fillRect(QRectF(15, 6, 2.5, 14), QColor(color_hex))
        elif icon_type == "register":  # Add User
            p.drawEllipse(QPointF(9, 8), 3.5, 3.5)
            path1 = QPainterPath()
            path1.arcMoveTo(QRectF(3, 14, 12, 8), 0)
            path1.arcTo(QRectF(3, 14, 12, 8), 0, 180)
            p.drawPath(path1)
            p.drawLine(17, 10, 21, 10)
            p.drawLine(19, 8, 19, 12)
        elif icon_type == "settings":  # Gear
            p.drawEllipse(QPointF(12, 12), 4, 4)
            for angle in range(0, 360, 45):
                p.save()
                p.translate(12, 12)
                p.rotate(angle)
                p.drawLine(0, -6.5, 0, -8.5)
                p.restore()
        elif icon_type == "sidebar_collapse":  # Simple Clean Left Arrow <
            path = QPainterPath()
            path.moveTo(14.5, 6.5)
            path.lineTo(9.5, 12)
            path.lineTo(14.5, 17.5)
            p.drawPath(path)
        elif icon_type == "sidebar_expand":  # Simple Clean Right Arrow >
            path = QPainterPath()
            path.moveTo(9.5, 6.5)
            path.lineTo(14.5, 12)
            path.lineTo(9.5, 17.5)
            p.drawPath(path)
        elif icon_type == "menu":  # Hamburger
            p.drawLine(5, 7, 19, 7)
            p.drawLine(5, 12, 19, 12)
            p.drawLine(5, 17, 19, 17)
        elif icon_type == "chevron_left":
            path = QPainterPath()
            path.moveTo(15, 6)
            path.lineTo(9, 12)
            path.lineTo(15, 18)
            p.drawPath(path)
        elif icon_type == "chevron_right":
            path = QPainterPath()
            path.moveTo(9, 6)
            path.lineTo(15, 12)
            path.lineTo(9, 18)
            p.drawPath(path)

        p.end()
        return pix

    icon = QIcon()
    # Normal state: unselected
    icon.addPixmap(_draw_pixmap(color_normal), QIcon.Normal, QIcon.Off)
    # Hover / Active state: unselected
    icon.addPixmap(_draw_pixmap("#F0F6FC"), QIcon.Active, QIcon.Off)
    # Selected / Checked state
    icon.addPixmap(_draw_pixmap(color_active), QIcon.Normal, QIcon.On)
    icon.addPixmap(_draw_pixmap(color_active), QIcon.Active, QIcon.On)
    return icon
