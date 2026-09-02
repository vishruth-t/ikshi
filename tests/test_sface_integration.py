import numpy as np
import pytest
from recognition.sface_model import SFaceRecognizer
from ui.workers.recognition_worker import RecognitionWorker
from unittest.mock import MagicMock

def test_sface_match_constants():
    sface = SFaceRecognizer()
    if sface.is_loaded():
        v1 = np.random.randn(1, 128).astype(np.float32)
        v2 = np.random.randn(1, 128).astype(np.float32)
        score = sface.match(v1, v2, metric="cosine")
        assert isinstance(score, float)

def test_recognition_worker_processing_flag_reset():
    detector = MagicMock()
    sface = MagicMock()
    matcher = MagicMock()
    attendance_service = MagicMock()

    detector.is_loaded.return_value = False
    sface.is_loaded.return_value = False

    worker = RecognitionWorker(detector, sface, matcher, attendance_service)
    
    # Process frame 1
    worker.process_frame(np.zeros((480, 640, 3), dtype=np.uint8))
    assert worker._is_processing is False

    # Process frame 2 - should not be locked out
    worker.process_frame(np.zeros((480, 640, 3), dtype=np.uint8))
    assert worker._is_processing is False


def test_recognition_worker_dual_frames_liveness():
    from vision.face_detector import DetectedFace
    from database.models import RecognitionResult
    from config.settings import settings

    detector = MagicMock()
    sface = MagicMock()
    matcher = MagicMock()
    attendance_service = MagicMock()

    detector.is_loaded.return_value = True
    sface.is_loaded.return_value = True

    # Mock face detection
    fake_face = DetectedFace(
        bbox=(100, 100, 100, 100),
        landmarks=np.zeros((5, 2)),
        score=0.95,
        raw_face_data=np.zeros(15)
    )
    detector.detect.return_value = [fake_face]
    sface.align_crop.return_value = np.zeros((112, 112, 3), dtype=np.uint8)
    sface.extract_feature.return_value = np.zeros((1, 128), dtype=np.float32)

    matcher.find_best_match.return_value = RecognitionResult(
        student_id=42,
        name="Alice",
        similarity=0.92,
        bbox=(100, 100, 100, 100)
    )

    worker = RecognitionWorker(detector, sface, matcher, attendance_service)
    worker.temporal_tracker.required_frames = 1

    settings.enable_ir_liveness = True
    settings.ir_liveness_threshold = 0.5

    rgb_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    ir_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    # Mock liveness detector
    worker.liveness_detector.evaluate = MagicMock()
    from vision.liveness_ir import LivenessResult
    worker.liveness_detector.evaluate.return_value = LivenessResult(
        passed=False,
        score=0.2,
        texture_score=0.1,
        reflectance_score=0.1,
        motion_score=0.5,
        status="failed",
        message="Spoof detected"
    )

    # Track emitted attendance events
    emitted_events = []
    worker.attendance_event.connect(lambda msg, ok: emitted_events.append((msg, ok)))

    worker.process_frames(rgb_frame, ir_frame)

    # Attendance service must NOT have been called to record attendance
    attendance_service.process_recognition.assert_not_called()
    # Failure event should be emitted
    assert len(emitted_events) == 1
    assert emitted_events[0][1] is False
    assert "Liveness check failed" in emitted_events[0][0]

    settings.enable_ir_liveness = False

