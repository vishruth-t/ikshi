import cv2
import numpy as np
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from typing import List, Optional
from database.models import RecognitionResult
from vision.image_utils import cv_to_qimage

class CameraViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(480, 320)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 12px;
            }
        """)
        self.layout.addWidget(self.image_label)

        self.latest_frame: Optional[np.ndarray] = None
        self.latest_results: List[RecognitionResult] = []

    @Slot(np.ndarray)
    def update_frame(self, frame: np.ndarray):
        self.latest_frame = frame
        self._render()

    @Slot(list)
    def update_recognition_results(self, results: List[RecognitionResult]):
        self.latest_results = results
        self._render()

    def _draw_hud_corners(self, img: np.ndarray, x: int, y: int, w: int, h: int, color: tuple, thickness: int = 2, corner_len: int = 20):
        """Draw sleek modern HUD corner brackets around face."""
        corner_len = max(12, min(corner_len, w // 4, h // 4))
        
        # Subtle semi-transparent box outline
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 1)
        cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

        # Top-Left Corner
        cv2.line(img, (x, y), (x + corner_len, y), color, thickness)
        cv2.line(img, (x, y), (x, y + corner_len), color, thickness)

        # Top-Right Corner
        cv2.line(img, (x + w, y), (x + w - corner_len, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + corner_len), color, thickness)

        # Bottom-Left Corner
        cv2.line(img, (x, y + h), (x + corner_len, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - corner_len), color, thickness)

        # Bottom-Right Corner
        cv2.line(img, (x + w, y + h), (x + w - corner_len, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - corner_len), color, thickness)

    def _render(self):
        if self.latest_frame is None:
            return

        img = self.latest_frame.copy()
        img_h, img_w = img.shape[:2]

        # Draw bounding boxes and text overlays
        for res in self.latest_results:
            if res.bbox is None:
                continue

            x, y, w, h = res.bbox
            x = max(0, min(img_w - 1, x))
            y = max(0, min(img_h - 1, y))
            w = max(1, min(img_w - x, w))
            h = max(1, min(img_h - y, h))

            if res.confirmed and res.student_id is not None:
                color = (46, 204, 113) # Emerald Green (BGR)
                label_text = f" VERIFIED: {res.name} ({int(res.similarity * 100)}%)"
            elif res.student_id is not None:
                color = (0, 191, 255) # Deep Sky Blue / Amber
                label_text = f" CONFIRMING: {res.name}..."
            elif res.name in ["Sample Target", "Adjust Position"]:
                color = (46, 204, 113) if res.confirmed else (245, 158, 11)
                label_text = f" {res.name}"
            else:
                color = (80, 80, 240) # Crimson / Red
                label_text = f" UNRECOGNIZED"

            # Draw HUD corner accents
            self._draw_hud_corners(img, x, y, w, h, color, thickness=3, corner_len=24)

            # Draw sleek translucent label pill
            font_scale = 0.55
            thickness = 2
            (txt_w, txt_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_DUPLEX, font_scale, 1)
            
            badge_y1 = max(0, y - txt_h - 14)
            badge_y2 = y
            badge_x1 = x
            badge_x2 = min(img_w, x + txt_w + 20)

            # Translucent badge background
            overlay = img.copy()
            cv2.rectangle(overlay, (badge_x1, badge_y1), (badge_x2, badge_y2), (15, 23, 42), -1)
            cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)

            # Left color bar accent on badge
            cv2.rectangle(img, (badge_x1, badge_y1), (badge_x1 + 4, badge_y2), color, -1)

            # Badge Text
            cv2.putText(
                img,
                label_text,
                (badge_x1 + 8, badge_y2 - 6),
                cv2.FONT_HERSHEY_DUPLEX,
                font_scale,
                (248, 250, 252),
                1,
                cv2.LINE_AA
            )

        qimg = cv_to_qimage(img)
        pixmap = QPixmap.fromImage(qimg)

        # Scale pixmap smoothly to fit view
        target_size = self.image_label.size()
        if target_size.width() > 10 and target_size.height() > 10:
            scaled_pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()

