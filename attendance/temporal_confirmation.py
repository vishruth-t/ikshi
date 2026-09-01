import logging
from typing import Dict, Optional
from database.models import RecognitionResult
from config.settings import settings

logger = logging.getLogger(__name__)

class TemporalConfirmationTracker:
    def __init__(self, required_frames: Optional[int] = None):
        self.required_frames = required_frames or settings.confirmation_frames
        self.current_candidate_id: Optional[int] = None
        self.consecutive_count: int = 0
        self.last_result: Optional[RecognitionResult] = None

    def process_result(self, result: RecognitionResult) -> RecognitionResult:
        """
        Processes frame recognition result and applies temporal stability logic.
        Updates result.confirmed flag to True when confirmed across N frames.
        """
        student_id = result.student_id

        if student_id is None or result.similarity < settings.recognition_threshold:
            # Reset tracking if unknown or below threshold
            self.current_candidate_id = None
            self.consecutive_count = 0
            result.confirmed = False
            return result

        if student_id == self.current_candidate_id:
            self.consecutive_count += 1
        else:
            self.current_candidate_id = student_id
            self.consecutive_count = 1

        if self.consecutive_count >= self.required_frames:
            result.confirmed = True
            logger.debug(f"Identity student_id={student_id} confirmed after {self.consecutive_count} frames.")
        else:
            result.confirmed = False

        self.last_result = result
        return result

    def reset(self):
        self.current_candidate_id = None
        self.consecutive_count = 0
        self.last_result = None
