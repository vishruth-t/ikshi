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

def validate_face_sample(image: np.ndarray, bbox: Tuple[int, int, int, int], num_detected_faces: int) -> Tuple[bool, str, str]:
    """
    Comprehensive quality and positioning checks for enrollment:
    1. Single face check
    2. Bounds & Centering check
    3. Distance / Face size check (too far / too close)
    4. Lighting / Brightness check
    5. Blur / Focus check

    Returns:
        (is_valid: bool, title: str, subtitle: str)
    """
    if num_detected_faces == 0:
        return False, "No face detected", "Make sure your face is clearly visible and there is enough lighting."
    
    if num_detected_faces > 1:
        return False, "Multiple faces detected", "Only one person should be visible during registration."

    x, y, w, h = bbox
    img_h, img_w = image.shape[:2]

    # Bounds check (partially out of frame)
    if x < 0 or y < 0 or (x + w) > img_w or (y + h) > img_h:
        return False, "Center your face", "Move your head left, right, up, or down until your face is centered."

    # Distance / Size check: Too far (too small)
    if w < max(settings.min_face_size, 90) or h < max(settings.min_face_size, 90):
        return False, "Move closer", "Move slightly closer to the camera until your face fits inside the guide."

    # Distance / Size check: Too close (too large)
    face_area = w * h
    frame_area = img_w * img_h
    if face_area / frame_area > 0.55 or w > (img_w * 0.75):
        return False, "Move farther away", "Move slightly back so your entire face fits inside the guide."

    # Centering check: Face center relative to frame center (tolerance: 28% of frame dimension)
    face_center_x = x + (w / 2.0)
    face_center_y = y + (h / 2.0)
    frame_center_x = img_w / 2.0
    frame_center_y = img_h / 2.0
    if abs(face_center_x - frame_center_x) > (img_w * 0.28) or abs(face_center_y - frame_center_y) > (img_h * 0.28):
        return False, "Center your face", "Move your head left, right, up, or down until your face is centered."

    # Face crop extraction for lighting and blur checks
    face_crop = image[max(0, y):min(img_h, y+h), max(0, x):min(img_w, x+w)]
    if face_crop.size == 0:
        return False, "No face detected", "Make sure your face is clearly visible."

    # Lighting / Brightness check
    gray_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY) if len(face_crop.shape) == 3 else face_crop
    mean_brightness = float(np.mean(gray_crop))
    if mean_brightness < 40.0:
        return False, "Improve the lighting", "Move to a brighter area and make sure your face is clearly visible."

    # Blur check
    blur_score = calculate_blur(face_crop)
    if blur_score < settings.blur_threshold:
        return False, "Hold still", "Keep your head steady while we capture your facial data."

    return True, "Hold still", "Keep your face centered while we capture your facial data."


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

