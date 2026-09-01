import numpy as np
import logging
from typing import List
from PySide6.QtCore import QObject, Slot, Signal
from vision.face_detector import FaceDetector
from recognition.sface_model import SFaceRecognizer
from recognition.matcher import FaceMatcher
from attendance.temporal_confirmation import TemporalConfirmationTracker
from attendance.attendance_service import AttendanceService
from database.models import RecognitionResult

logger = logging.getLogger(__name__)

class RecognitionWorker(QObject):
    results_ready = Signal(list) # List of RecognitionResult objects
    attendance_event = Signal(str, bool) # (message, success)

    def __init__(
        self,
        detector: FaceDetector,
        sface: SFaceRecognizer,
        matcher: FaceMatcher,
        attendance_service: AttendanceService
    ):
        super().__init__()
        self.detector = detector
        self.sface = sface
        self.matcher = matcher
        self.attendance_service = attendance_service
        self.temporal_tracker = TemporalConfirmationTracker()
        self._is_processing = False

    @Slot(np.ndarray)
    def process_frame(self, frame: np.ndarray):
        if self._is_processing or frame is None:
            return

        self._is_processing = True
        try:
            results: List[RecognitionResult] = []

            if not self.detector.is_loaded() or not self.sface.is_loaded():
                self.results_ready.emit([])
                return

            detected_faces = self.detector.detect(frame)

            if not detected_faces:
                self.temporal_tracker.reset()
                self.results_ready.emit([])
                return

            for face in detected_faces:
                aligned_crop = self.sface.align_crop(frame, face.raw_face_data)
                if aligned_crop is None:
                    continue

                feature = self.sface.extract_feature(aligned_crop)
                if feature is None:
                    continue

                # Match identity
                result = self.matcher.find_best_match(feature, bbox=face.bbox)

                # Temporal confirmation
                confirmed_result = self.temporal_tracker.process_result(result)

                # Record attendance if confirmed
                if confirmed_result.confirmed and confirmed_result.student_id is not None:
                    success, msg = self.attendance_service.process_recognition(confirmed_result)
                    if success:
                        self.attendance_event.emit(msg, True)

                results.append(confirmed_result)

            self.results_ready.emit(results)
        except Exception as e:
            logger.error(f"Error in RecognitionWorker: {e}")
        finally:
            self.is_processing = False
