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
        self.show_standby_placeholder()

    def show_standby_placeholder(
        self,
        main_text: str = "Session in Standby",
        sub_text: str = "Click 'Start Session' to activate live camera feeds"
    ):
        """Render clean standby graphic when cameras are offline or in standby."""
        self.latest_frame = None
        self.latest_results = []

        h, w = 480, 640
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (w, h), (13, 17, 23), -1)

        cx, cy = w // 2, h // 2 - 25
        # Standby camera aperture icon
        cv2.circle(frame, (cx, cy), 38, (48, 54, 61), 2)
        cv2.circle(frame, (cx, cy), 14, (48, 54, 61), -1)

        (w1, h1), _ = cv2.getTextSize(main_text, cv2.FONT_HERSHEY_DUPLEX, 0.70, 1)
        cv2.putText(frame, main_text, (cx - w1 // 2, cy + 65), cv2.FONT_HERSHEY_DUPLEX, 0.70, (240, 246, 252), 1, cv2.LINE_AA)

        (w2, h2), _ = cv2.getTextSize(sub_text, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)
        cv2.putText(frame, sub_text, (cx - w2 // 2, cy + 96), cv2.FONT_HERSHEY_DUPLEX, 0.45, (139, 148, 158), 1, cv2.LINE_AA)

        qimg = cv_to_qimage(frame)
        pixmap = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap)

    def clear(self):
        self.show_standby_placeholder()

    @Slot(np.ndarray)
    def update_frame(self, frame: np.ndarray):
        self.latest_frame = frame
        self._render()

    @Slot(list)
    def update_recognition_results(self, results: List[RecognitionResult]):
        self.latest_results = results
        self._render()

    def _draw_opencv_box(self, img: np.ndarray, x: int, y: int, w: int, h: int, color: tuple, label: str):
        """Draw classic OpenCV identifier box with corner accent brackets and solid label tag."""
        # 1. Main bounding rectangle
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
        
        # 2. Corner brackets
        corner_len = max(10, min(22, w // 4, h // 4))
        thickness = 3
        # Top-Left
        cv2.line(img, (x, y), (x + corner_len, y), color, thickness)
        cv2.line(img, (x, y), (x, y + corner_len), color, thickness)
        # Top-Right
        cv2.line(img, (x + w, y), (x + w - corner_len, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + corner_len), color, thickness)
        # Bottom-Left
        cv2.line(img, (x, y + h), (x + corner_len, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - corner_len), color, thickness)
        # Bottom-Right
        cv2.line(img, (x + w, y + h), (x + w - corner_len, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - corner_len), color, thickness)
        
        # 3. Label tag
        font_scale = 0.5
        (txt_w, txt_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        tag_y = max(txt_h + 8, y)
        cv2.rectangle(img, (x, tag_y - txt_h - 6), (x + txt_w + 10, tag_y), color, -1)
        cv2.putText(img, label, (x + 5, tag_y - 4), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)

    def _render(self):
        if self.latest_frame is None:
            return

        img = self.latest_frame.copy()
        img_h, img_w = img.shape[:2]

        # Draw OpenCV identifier bounding boxes
        for res in self.latest_results:
            if res.bbox is None:
                continue

            x, y, w, h = res.bbox
            x = max(0, min(img_w - 1, x))
            y = max(0, min(img_h - 1, y))
            w = max(1, min(img_w - x, w))
            h = max(1, min(img_h - y, h))

            # Visual status styling considering recognition and IR liveness
            if res.liveness_passed is False and res.student_id is not None:
                color = (45, 80, 245) # Red-Amber (BGR)
                score_tag = f" ({int(res.liveness_score * 100)}%)" if res.liveness_score is not None else ""
                label_text = f"{res.name} • Spoof Detected{score_tag}"
            elif res.confirmed and res.student_id is not None:
                color = (67, 160, 46) # Green (BGR)
                liveness_tag = " • Live" if res.liveness_passed is True and res.liveness_status == "passed" else ""
                pose_tag = f" • {res.matched_pose}" if res.matched_pose else ""
                label_text = f"{res.name} ({int(res.similarity * 100)}%{pose_tag}){liveness_tag}"
            elif res.student_id is not None:
                color = (247, 166, 203) # Mauve #cba6f7 (BGR)
                pose_tag = f" ({res.matched_pose})" if res.matched_pose else ""
                label_text = f"Verifying {res.name}{pose_tag}..."
            elif res.name in ["Target Ready", "Sample Target", "Adjust Position", "Hold still", "Move closer", "Center your face", "Position your face"]:
                color = (67, 160, 46) if res.confirmed else (245, 158, 11)
                label_text = res.name
            else:
                color = (73, 81, 248) # Red (BGR)
                label_text = "Unknown"

            self._draw_opencv_box(img, x, y, w, h, color, label_text)


        # Scale Pixmap to fit label preserving aspect ratio
        qimg = cv_to_qimage(img)
        pixmap = QPixmap.fromImage(qimg)
        
        target_size = self.image_label.size()
        if target_size.width() > 10 and target_size.height() > 10:
            scaled = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setPixmap(pixmap)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()
