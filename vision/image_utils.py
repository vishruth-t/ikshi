import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap
from typing import Tuple, Optional
from config.settings import settings

def calculate_blur(image: np.ndarray) -> float:
    """
    Calculate Laplacian variance as a measure of image focus/blur.
    Higher value means sharper image.
    """
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def validate_face_sample(image: np.ndarray, bbox: Tuple[int, int, int, int], num_detected_faces: int) -> Tuple[bool, str]:
    """
    Quality checks for enrollment sample:
    1. Single face check
    2. Face size check
    3. Blur check
    4. Centering / bounds check
    """
    if num_detected_faces == 0:
        return False, "No face detected in frame."
    if num_detected_faces > 1:
        return False, "Multiple faces detected. Only one face should be visible."

    x, y, w, h = bbox
    img_h, img_w = image.shape[:2]

    # Face size check
    if w < settings.min_face_size or h < settings.min_face_size:
        return False, f"Face too small ({w}x{h}). Move closer to camera."

    # Bounds check
    if x < 0 or y < 0 or (x + w) > img_w or (y + h) > img_h:
        return False, "Face is partially out of frame."

    # Face crop blur check
    face_crop = image[max(0, y):min(img_h, y+h), max(0, x):min(img_w, x+w)]
    blur_score = calculate_blur(face_crop)
    if blur_score < settings.blur_threshold:
        return False, f"Face image too blurry (score: {blur_score:.1f}). Hold still."

    return True, "Face quality acceptable."

def cv_to_qimage(cv_img: np.ndarray) -> QImage:
    """Convert OpenCV BGR or Grayscale image to PySide6 QImage."""
    if cv_img is None or cv_img.size == 0:
        return QImage()
    
    if len(cv_img.shape) == 2:
        h, w = cv_img.shape
        bytes_per_line = w
        return QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
    
    h, w, ch = cv_img.shape
    bytes_per_line = ch * w
    rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    return QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)

def cv_to_qpixmap(cv_img: np.ndarray) -> QPixmap:
    """Convert OpenCV BGR image to PySide6 QPixmap."""
    qimg = cv_to_qimage(cv_img)
    return QPixmap.fromImage(qimg)

