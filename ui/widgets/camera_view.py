import cv2
import numpy as np
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFont
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
        self.image_label.setStyleSheet("background-color: #121212; border-radius: 8px;")
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

    def _render(self):
        if self.latest_frame is None:
            return

        img = self.latest_frame.copy()

        # Draw bounding boxes and text overlays
        for res in self.latest_results:
            if res.bbox is None:
                continue

            x, y, w, h = res.bbox
            if res.confirmed and res.student_id is not None:
                color = (0, 220, 100) # Green (BGR)
                label_text = f"✓ {res.name} ({res.similarity:.2f})"
            elif res.student_id is not None:
                color = (0, 200, 255) # Amber/Yellow
                label_text = f"Confirming {res.name}... ({res.similarity:.2f})"
            else:
                color = (50, 50, 240) # Red
                label_text = f"UNKNOWN ({res.similarity:.2f})"

            # Bounding box
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)

            # Label box background
            (txt_w, txt_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (x, max(0, y - txt_h - 10)), (x + txt_w + 10, y), color, -1)
            cv2.putText(img, label_text, (x + 5, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        qimg = cv_to_qimage(img)
        pixmap = QPixmap.fromImage(qimg)

        # Scale pixmap to fit widget keeping aspect ratio
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
