import numpy as np
import pytest
from vision.image_utils import calculate_blur, validate_face_sample, cv_to_qimage, cv_to_qpixmap
from config.settings import settings

def test_calculate_blur_on_sharp_and_blurry_images():
    # Crisp checkerboard / random gradient
    sharp = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    sharp_score = calculate_blur(sharp)
    assert sharp_score > 0.0

    # Flat uniform image -> 0 blur
    flat = np.ones((100, 100, 3), dtype=np.uint8) * 128
    flat_score = calculate_blur(flat)
    assert flat_score == 0.0

def test_validate_face_sample_conditions():
    img = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # 1. No faces detected
    valid, title, subtitle = validate_face_sample(img, (0, 0, 0, 0), 0)
    assert valid is False
    assert "No face detected" in title

    # 2. Multiple faces detected
    valid, title, subtitle = validate_face_sample(img, (100, 100, 150, 150), 2)
    assert valid is False
    assert "Multiple faces detected" in title

    # 3. Face too small / too far
    valid, title, subtitle = validate_face_sample(img, (100, 100, 30, 30), 1)
    assert valid is False
    assert "Move closer" in title

    # 4. Out of frame bounds
    valid, title, subtitle = validate_face_sample(img, (-10, 100, 150, 150), 1)
    assert valid is False
    assert "Center your face" in title


def test_cv_to_qimage_and_qpixmap():
    bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    qimg = cv_to_qimage(bgr)
    assert not qimg.isNull()
    assert qimg.width() == 100
    assert qimg.height() == 100

    qpixmap = cv_to_qpixmap(bgr)
    assert not qpixmap.isNull()
    assert qpixmap.width() == 100
    assert qpixmap.height() == 100
