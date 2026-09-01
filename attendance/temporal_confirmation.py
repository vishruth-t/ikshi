import logging
from typing import Dict, Optional, Set
from database.models import RecognitionResult
from config.settings import settings

logger = logging.getLogger(__name__)

class TemporalConfirmationTracker:
    def __init__(self, required_frames: Optional[int] = None):
        self.required_frames = required_frames or settings.confirmation_frames
        self.candidate_counts: Dict[int, int] = {}
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
            # Result is unknown or below threshold
            self.current_candidate_id = None
            self.consecutive_count = 0
            result.confirmed = False
            self.last_result = result
            return result


        # Increment consecutive frame count for this student
        prev_count = self.candidate_counts.get(student_id, 0)
        new_count = prev_count + 1
        self.candidate_counts[student_id] = new_count

        self.current_candidate_id = student_id
        self.consecutive_count = new_count

        if new_count >= self.required_frames:
            result.confirmed = True
            logger.debug(f"Identity student_id={student_id} confirmed after {new_count} frames.")
        else:
            result.confirmed = False

        self.last_result = result
        return result

    def decay_missing(self, active_ids: Set[int]):
        """
        Decay or reset candidates who were not detected in the current frame batch.
        """
        keys_to_remove = []
        for sid in self.candidate_counts:
            if sid not in active_ids:
                keys_to_remove.append(sid)
        for sid in keys_to_remove:
            del self.candidate_counts[sid]

    def reset_student(self, student_id: int):
        """Reset counter for a specific student (e.g. after attendance is successfully marked)."""
        if student_id in self.candidate_counts:
            del self.candidate_counts[student_id]
        if self.current_candidate_id == student_id:
            self.current_candidate_id = None
            self.consecutive_count = 0

    def reset(self):
        self.candidate_counts.clear()
        self.current_candidate_id = None
        self.consecutive_count = 0
        self.last_result = None

