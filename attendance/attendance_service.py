import logging
from typing import Tuple, Optional
from datetime import datetime
from database.repositories import AttendanceRepository, StudentRepository
from database.models import Attendance, RecognitionResult
from attendance.session_manager import SessionManager

from config.settings import settings

logger = logging.getLogger(__name__)

class AttendanceService:
    def __init__(
        self,
        attendance_repo: AttendanceRepository,
        student_repo: StudentRepository,
        session_manager: SessionManager
    ):
        self.attendance_repo = attendance_repo
        self.student_repo = student_repo
        self.session_manager = session_manager

    def process_recognition(self, result: RecognitionResult) -> Tuple[bool, str]:
        """
        Record attendance if student is valid, active, session active, not already marked,
        and passes IR anti-spoofing liveness check (if enabled).
        Returns (success: bool, status_message: str)
        """
        if not result.confirmed or result.student_id is None:
            return False, "Unconfirmed or unknown identity."

        current_session = self.session_manager.get_active_session()
        if not current_session:
            return False, "No active attendance session."

        student = self.student_repo.get_by_id(result.student_id)
        if not student or not student.active:
            return False, f"Student ID {result.student_id} is inactive or non-existent."

        # IR Anti-Spoofing Liveness Gate
        if settings.enable_ir_liveness and result.liveness_passed is False:
            score_str = f"{int(result.liveness_score * 100)}%" if result.liveness_score is not None else "N/A"
            logger.warning(
                f"Attendance blocked for {student.name} ({student.student_number}): "
                f"IR liveness check failed ({result.liveness_message}, score={score_str})"
            )
            return False, f"Liveness check failed for {student.name} ({result.liveness_message or 'Spoof detected'})"

        # Application-level duplicate check
        if self.attendance_repo.is_marked(current_session.id, student.id):
            return False, f"Attendance already marked for {student.name}."

        attendance_record = Attendance(
            session_id=current_session.id,
            student_id=student.id,
            marked_at=datetime.now().isoformat(),
            status="Present",
            similarity=result.similarity,
            liveness_score=result.liveness_score,
            liveness_passed=result.liveness_passed
        )

        inserted = self.attendance_repo.record_attendance(attendance_record)
        if inserted:
            logger.info(f"Recorded attendance for {student.name} (Session {current_session.id})")
            return True, f"Attendance marked for {student.name} ({student.student_number})"
        else:
            return False, f"Duplicate attendance entry prevented for {student.name}."
