import pytest
import numpy as np
import cv2
from vision.liveness_ir import IRLivenessDetector, LivenessResult
from config.settings import settings


@pytest.fixture
def detector():
    return IRLivenessDetector()


def create_synthetic_live_face(size=(100, 100)) -> np.ndarray:
    """Simulate realistic human face texture in IR (radial 3D gradients, facial features, noise)."""
    h, w = size
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2.0, h / 2.0
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    radial = 140.0 - 45.0 * (r / (min(h, w) / 2.0))
    noise = np.random.normal(0, 10, (h, w))
    face = np.clip(radial + noise, 30, 210).astype(np.uint8)
    return face


def create_synthetic_flat_photo(size=(100, 100)) -> np.ndarray:
    """Simulate flat 2D printed photo with minimal texture variance."""
    h, w = size
    # Flat uniform color with negligible noise
    flat = np.full((h, w), 120, dtype=np.uint8)
    return flat


def create_synthetic_screen_glare(size=(100, 100)) -> np.ndarray:
    """Simulate harsh specular glare from phone screen reflection."""
    h, w = size
    img = np.full((h, w), 80, dtype=np.uint8)
    # 40% of the image is saturated screen glare
    img[:int(h * 0.6), :int(w * 0.7)] = 255
    return img


def create_synthetic_screen_blackout(size=(100, 100)) -> np.ndarray:
    """Simulate turned-off screen or IR-absorbing LCD."""
    h, w = size
    return np.full((h, w), 5, dtype=np.uint8)


def test_liveness_disabled(detector):
    settings.enable_ir_liveness = False
    rgb_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)
    bbox = (100, 100, 150, 150)

    res = detector.evaluate(rgb_frame, ir_frame, bbox)
    assert res.passed is True
    assert res.status == "disabled"
    assert "Disabled" in res.message


def test_liveness_ir_unavailable_graceful_fallback(detector):
    settings.enable_ir_liveness = True
    rgb_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    bbox = (100, 100, 150, 150)

    # IR frame is None
    res = detector.evaluate(rgb_frame, None, bbox)
    assert res.passed is True
    assert res.status == "disabled"
    assert "Unavailable" in res.message


def test_liveness_live_face_passes(detector):
    settings.enable_ir_liveness = True
    settings.ir_liveness_threshold = 0.40

    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    # Place live face in IR frame center
    live_crop = create_synthetic_live_face((120, 120))
    ir_frame[100:220, 200:320, 0] = live_crop
    ir_frame[100:220, 200:320, 1] = live_crop
    ir_frame[100:220, 200:320, 2] = live_crop

    # RGB bbox corresponding to that region
    # IR center = (260, 160) -> norm = (260/640, 160/360) -> RGB = (520, 320)
    rgb_bbox = (400, 200, 240, 240)

    res = detector.evaluate(rgb_frame, ir_frame, rgb_bbox, student_id=1)
    assert res.score > 0.40
    assert res.passed is True
    assert res.status == "passed"


def test_liveness_flat_photo_fails(detector):
    settings.enable_ir_liveness = True
    settings.ir_liveness_threshold = 0.50

    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    # Place completely flat photo in IR
    flat_crop = create_synthetic_flat_photo((120, 120))
    ir_frame[100:220, 200:320, 0] = flat_crop
    ir_frame[100:220, 200:320, 1] = flat_crop
    ir_frame[100:220, 200:320, 2] = flat_crop

    rgb_bbox = (400, 200, 240, 240)

    res = detector.evaluate(rgb_frame, ir_frame, rgb_bbox, student_id=2)
    assert res.passed is False
    assert res.status == "failed"


def test_liveness_screen_glare_fails(detector):
    settings.enable_ir_liveness = True
    settings.ir_liveness_threshold = 0.45

    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    glare_crop = create_synthetic_screen_glare((120, 120))
    ir_frame[100:220, 200:320, 0] = glare_crop
    ir_frame[100:220, 200:320, 1] = glare_crop
    ir_frame[100:220, 200:320, 2] = glare_crop

    rgb_bbox = (400, 200, 240, 240)

    res = detector.evaluate(rgb_frame, ir_frame, rgb_bbox, student_id=3)
    assert res.passed is False
    assert "Glare" in res.message or res.status == "failed"


def test_liveness_screen_blackout_fails(detector):
    settings.enable_ir_liveness = True
    settings.ir_liveness_threshold = 0.45

    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    blackout_crop = create_synthetic_screen_blackout((120, 120))
    ir_frame[100:220, 200:320, 0] = blackout_crop
    ir_frame[100:220, 200:320, 1] = blackout_crop
    ir_frame[100:220, 200:320, 2] = blackout_crop

    rgb_bbox = (400, 200, 240, 240)

    res = detector.evaluate(rgb_frame, ir_frame, rgb_bbox, student_id=4)
    assert res.passed is False
    assert "Blackout" in res.message or res.status == "failed"


def test_map_bbox_to_ir(detector):
    settings.ir_fov_scale_x = 1.0
    settings.ir_fov_scale_y = 1.0
    settings.ir_offset_x = 0
    settings.ir_offset_y = 0

    rgb_shape = (720, 1280)
    ir_shape = (360, 640)
    rgb_bbox = (320, 180, 640, 360) # Center half of RGB frame

    ir_bbox = detector.map_bbox_to_ir(rgb_bbox, rgb_shape, ir_shape)
    # Expected center at (320, 180), size (320, 180) -> (160, 90, 320, 180)
    assert abs(ir_bbox[0] - 160) <= 2
    assert abs(ir_bbox[1] - 90) <= 2
    assert abs(ir_bbox[2] - 320) <= 2
    assert abs(ir_bbox[3] - 180) <= 2


def test_temporal_motion_tracking(detector):
    settings.enable_ir_liveness = True
    # Frame 1
    crop1 = create_synthetic_live_face()
    # Frame 2 with slight natural live micro-motion delta
    crop2 = np.clip(crop1.astype(np.int16) + np.random.randint(-3, 4, crop1.shape), 0, 255).astype(np.uint8)

    s1 = detector._compute_motion_score(crop1, tracker_key="user_1")
    assert s1 == 0.5 # Neutral on initial frame

    s2 = detector._compute_motion_score(crop2, tracker_key="user_1")
    assert s2 >= 0.30 # Non-zero motion variance

    # Static identical frame repeated
    detector._compute_motion_score(crop2, tracker_key="user_1")
    s_static = detector._compute_motion_score(crop2, tracker_key="user_1")
    assert s_static <= 0.20 # Static penalty

    detector.reset_history("user_1")
    assert "user_1" not in detector._history


def test_liveness_ir_biometric_cross_check(detector):
    from unittest.mock import MagicMock
    settings.enable_ir_liveness = True
    settings.ir_liveness_threshold = 0.40

    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    live_crop = create_synthetic_live_face((120, 120))
    ir_frame[100:220, 200:320, 0] = live_crop
    ir_frame[100:220, 200:320, 1] = live_crop
    ir_frame[100:220, 200:320, 2] = live_crop

    rgb_bbox = (400, 200, 240, 240)

    # Mock SFace recognizer
    mock_sface = MagicMock()
    mock_sface.extract_feature.return_value = np.random.randn(1, 128).astype(np.float32)
    mock_sface.match.return_value = 0.85 # High matching score

    enrolled_ir = [np.random.randn(128).astype(np.float32)]

    res = detector.evaluate(
        rgb_frame,
        ir_frame,
        rgb_bbox,
        student_id=5,
        enrolled_ir_embeddings=enrolled_ir,
        sface_recognizer=mock_sface
    )
    assert res.passed is True
    assert res.details.get("ir_biometric") == 0.85


def test_liveness_phone_bezel_detected_fails(detector):
    settings.enable_ir_liveness = True
    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    face = create_synthetic_live_face((120, 120))
    # Draw straight vertical device bezels on the IR crop
    cv2.line(face, (15, 5), (15, 115), 245, 2)
    cv2.line(face, (105, 5), (105, 115), 245, 2)

    ir_frame[100:220, 200:320, 0] = face
    ir_frame[100:220, 200:320, 1] = face
    ir_frame[100:220, 200:320, 2] = face
    rgb_bbox = (400, 200, 240, 240)

    res = detector.evaluate(rgb_frame, ir_frame, rgb_bbox, student_id=6)
    assert res.passed is False
    assert "Bezel" in res.message or "Spoof" in res.message


def test_liveness_tilted_screen_gradient_entropy_fails(detector):
    settings.enable_ir_liveness = True
    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    # Tilted flat glass surface creates planar unidirectional linear gradient
    planar_gradient = np.linspace(50, 130, 120, dtype=np.uint8)[:, None]
    screen_crop = np.repeat(planar_gradient, 120, axis=1)

    ir_frame[100:220, 200:320, 0] = screen_crop
    ir_frame[100:220, 200:320, 1] = screen_crop
    ir_frame[100:220, 200:320, 2] = screen_crop
    rgb_bbox = (400, 200, 240, 240)

    res = detector.evaluate(rgb_frame, ir_frame, rgb_bbox, student_id=7)
    assert res.passed is False
    assert "Spoof Detected" in res.message or "Flat" in res.message


def test_liveness_ir_biometric_mismatch_fails(detector):
    from unittest.mock import MagicMock
    settings.enable_ir_liveness = True
    settings.ir_liveness_threshold = 0.50

    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    live_crop = create_synthetic_live_face((120, 120))
    ir_frame[100:220, 200:320, 0] = live_crop
    ir_frame[100:220, 200:320, 1] = live_crop
    ir_frame[100:220, 200:320, 2] = live_crop
    rgb_bbox = (400, 200, 240, 240)

    # Mock SFace with very low matching score (0.08 - mismatching face)
    mock_sface = MagicMock()
    mock_sface.is_loaded.return_value = True
    mock_sface.align_crop.return_value = np.zeros((112, 112, 3), dtype=np.uint8)
    mock_sface.extract_feature.return_value = np.random.randn(1, 128).astype(np.float32)
    mock_sface.match.return_value = 0.08

    enrolled_ir = [np.random.randn(128).astype(np.float32)]

    res = detector.evaluate(
        rgb_frame,
        ir_frame,
        rgb_bbox,
        student_id=8,
        enrolled_ir_embeddings=enrolled_ir,
        sface_recognizer=mock_sface
    )
    assert res.passed is False
    assert "Mismatch" in res.message or res.status == "failed"


def test_liveness_horizontal_turn_planar_ramp_fails(detector):
    settings.enable_ir_liveness = True
    rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    # Monotonic linear ramp across columns (horizontal glass reflection)
    h, w = 120, 120
    col_ramp = np.linspace(40, 130, w, dtype=np.uint8)[None, :]
    turned_screen = np.repeat(col_ramp, h, axis=0)

    ir_frame[100:220, 200:320, 0] = turned_screen
    ir_frame[100:220, 200:320, 1] = turned_screen
    ir_frame[100:220, 200:320, 2] = turned_screen
    rgb_bbox = (400, 200, 240, 240)

    res = detector.evaluate(rgb_frame, ir_frame, rgb_bbox, student_id=9)
    assert res.passed is False
    assert "Ramp" in res.message or "Horizontal Turn" in res.message or res.status == "failed"



