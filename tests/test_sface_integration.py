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
