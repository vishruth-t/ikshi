import os
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QPen
from PySide6.QtCore import Qt, QRectF

def render_circular_avatar(
    image_path: str,
    size: int = 32,
    border_color: str = "#cba6f7",
    border_width: float = 1.2
) -> QPixmap:
    """Render a crisp, antialiased circular avatar pixmap from an image file."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    if not image_path or not os.path.exists(image_path):
        return pix

    src_pixmap = QPixmap(image_path)
    if src_pixmap.isNull():
        return pix

    # Scale with smooth transformation to cover size x size
    scaled = src_pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    sw, sh = scaled.width(), scaled.height()
    sx = max(0, (sw - size) // 2)
    sy = max(0, (sh - size) // 2)
    cropped = scaled.copy(sx, sy, size, size)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)

    # 1. Circular Mask
    path = QPainterPath()
    path.addEllipse(0.5, 0.5, size - 1, size - 1)
    p.setClipPath(path)
    p.drawPixmap(0, 0, cropped)

    # 2. Outer Smooth Antialiased Border Ring
    p.setClipping(False)
    if border_width > 0 and border_color:
        pen = QPen(QColor(border_color), border_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        offset = border_width / 2.0
        p.drawEllipse(QRectF(offset, offset, size - border_width, size - border_width))

    p.end()
    return pix
