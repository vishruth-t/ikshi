import numpy as np
import logging
from typing import List, Set, Optional
from PySide6.QtCore import QObject, Slot, Signal
from vision.face_detector import FaceDetector
from recognition.sface_model import SFaceRecognizer
from recognition.matcher import FaceMatcher
from attendance.temporal_confirmation import TemporalConfirmationTracker
from attendance.attendance_service import AttendanceService
from vision.liveness_ir import IRLivenessDetector, LivenessResult
from database.models import RecognitionResult
from database.repositories import SecurityAuditRepository
from config.settings import settings
import os
import cv2
from datetime import datetime

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
        self.liveness_detector = IRLivenessDetector()
        self._is_processing = False
        self._enabled = True
        self._last_spoof_log_time = 0.0

        # Initialize security audit repository
        self.security_repo = None
        if hasattr(self.attendance_service, "attendance_repo") and hasattr(self.attendance_service.attendance_repo, "db"):
            self.security_repo = SecurityAuditRepository(self.attendance_service.attendance_repo.db)

    @Slot(bool)
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if not enabled:
            self.temporal_tracker.reset()
            self.liveness_detector.reset_history()
            self.results_ready.emit([])

    def update_tracker_settings(self):
        """Update tracker required frames from global settings."""
        self.temporal_tracker.required_frames = settings.confirmation_frames

    @Slot(np.ndarray)
    def process_frame(self, frame: np.ndarray):
        """Single-frame slot for RGB only."""
        self.process_frames(frame, None)

    @Slot(np.ndarray, object)
    def process_frames(self, frame: np.ndarray, ir_frame: Optional[np.ndarray] = None):
        """Dual-frame slot handling RGB camera frame and optional secondary IR sensor frame."""
        if not self._enabled or self._is_processing or frame is None:
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

            active_ids: Set[int] = set()

            for face in detected_faces:
                aligned_crop = self.sface.align_crop(frame, face.raw_face_data)
                if aligned_crop is None:
                    continue

                feature = self.sface.extract_feature(aligned_crop)
                if feature is None:
                    continue

                # 1. Match identity
                result = self.matcher.find_best_match(feature, bbox=face.bbox)

                if result.student_id is not None:
                    active_ids.add(result.student_id)

                # 2. IR Anti-Spoofing & Liveness Evaluation
                if settings.enable_ir_liveness:
                    enrolled_ir = None
                    if result.student_id is not None and hasattr(self.matcher, "embedding_repo"):
                        enrolled_ir = self.matcher.embedding_repo.get_student_embeddings(
                            result.student_id,
                            model_name="SFace-IR"
                        )

                    liveness_res: LivenessResult = self.liveness_detector.evaluate(
                        rgb_frame=frame,
                        ir_frame=ir_frame,
                        rgb_bbox=face.bbox,
                        student_id=result.student_id,
                        enrolled_ir_embeddings=enrolled_ir,
                        sface_recognizer=self.sface,
                        face_detector=self.detector
                    )
                    result.liveness_score = liveness_res.score
                    result.liveness_passed = liveness_res.passed
                    result.liveness_status = liveness_res.status
                    result.liveness_message = liveness_res.message
                    result.ir_bbox = liveness_res.ir_bbox
                else:
                    result.liveness_score = 1.0
                    result.liveness_passed = True
                    result.liveness_status = "disabled"
                    result.liveness_message = ""

                # 3. Temporal confirmation
                confirmed_result = self.temporal_tracker.process_result(result)

                # 4. Record attendance if confirmed and liveness passes
                if confirmed_result.confirmed and confirmed_result.student_id is not None:
                    if settings.enable_ir_liveness and confirmed_result.liveness_passed is False:
                        msg = f"Liveness check failed for {confirmed_result.name} ({confirmed_result.liveness_message or 'Spoof detected'})"
                        self.attendance_event.emit(msg, False)
                        self._log_spoof_evidence(frame, ir_frame, confirmed_result, liveness_res if 'liveness_res' in locals() else None)
                    else:
                        success, msg = self.attendance_service.process_recognition(confirmed_result)
                        if success:
                            self.attendance_event.emit(msg, True)
                            # Reset tracking for this student so they don't trigger repeated events
                            self.temporal_tracker.reset_student(confirmed_result.student_id)
                            self.liveness_detector.reset_history(confirmed_result.student_id)
                        elif "Liveness" in msg:
                            self.attendance_event.emit(msg, False)

                results.append(confirmed_result)

            self.temporal_tracker.decay_missing(active_ids)
            self.results_ready.emit(results)
        except Exception as e:
            logger.error(f"Error in RecognitionWorker: {e}")
        finally:
            self._is_processing = False

    def _log_spoof_evidence(
        self,
        rgb_frame: np.ndarray,
        ir_frame: Optional[np.ndarray],
        result: RecognitionResult,
        liveness_res: Optional[LivenessResult]
    ):
        """Save forensic snapshot evidence and record security audit log (rate-limited to 1 per 3s)."""
        import time
        now = time.time()
        if now - self._last_spoof_log_time < 3.0 or self.security_repo is None:
            return
        self._last_spoof_log_time = now

        try:
            audit_dir = os.path.join(settings.BASE_DIR, "data", "security_audits")
            os.makedirs(audit_dir, exist_ok=True)
            ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            stu_id_tag = result.student_id or "unknown"

            rgb_path = os.path.join(audit_dir, f"spoof_RGB_{ts_str}_{stu_id_tag}.jpg")
            cv2.imwrite(rgb_path, rgb_frame)

            ir_path = None
            if ir_frame is not None and ir_frame.size > 0:
                ir_path = os.path.join(audit_dir, f"spoof_IR_{ts_str}_{stu_id_tag}.jpg")
                cv2.imwrite(ir_path, ir_frame)

            reason = result.liveness_message or "Spoof Detected"
            liveness_score = result.liveness_score or 0.0
            tex_score = liveness_res.texture_score if liveness_res else 0.0
            refl_score = liveness_res.reflectance_score if liveness_res else 0.0
            ent_score = liveness_res.details.get("entropy", 0.0) if (liveness_res and liveness_res.details) else 0.0
            mot_score = liveness_res.motion_score if liveness_res else 0.0

            self.security_repo.log_audit(
                reason=reason,
                matched_student_id=result.student_id,
                matched_name=result.name,
                liveness_score=liveness_score,
                texture_score=tex_score,
                reflectance_score=refl_score,
                entropy_score=ent_score,
                motion_score=mot_score,
                snapshot_path=rgb_path,
                ir_snapshot_path=ir_path
            )
            logger.warning(f"Forensic spoof snapshot saved to {rgb_path} ({reason})")
        except Exception as e:
            logger.debug(f"Error logging spoof forensic snapshot: {e}")

