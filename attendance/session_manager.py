import logging
from datetime import datetime
from typing import Optional, Dict, Any
from database.repositories import SessionRepository, StudentRepository, AttendanceRepository
from database.models import AttendanceSession

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(
        self,
        session_repo: SessionRepository,
        student_repo: StudentRepository,
        attendance_repo: AttendanceRepository
    ):
        self.session_repo = session_repo
        self.student_repo = student_repo
        self.attendance_repo = attendance_repo
        self.active_session: Optional[AttendanceSession] = None

    def start_session(self, subject: str, class_name: str) -> AttendanceSession:
        session = AttendanceSession(
            date=datetime.now().strftime("%Y-%m-%d"),
            subject=subject,
            class_name=class_name,
            started_at=datetime.now().isoformat()
        )
        self.active_session = self.session_repo.create_session(session)
        logger.info(f"Started session ID {self.active_session.id} for {class_name} - {subject}")
        return self.active_session

    def end_session(self) -> Optional[AttendanceSession]:
        if not self.active_session:
            return None
        ended_at = datetime.now().isoformat()
        self.session_repo.end_session(self.active_session.id, ended_at)
        self.active_session.ended_at = ended_at
        finished_session = self.active_session
        self.active_session = None
        logger.info(f"Ended session ID {finished_session.id}")
        return finished_session

    def get_active_session(self) -> Optional[AttendanceSession]:
        return self.active_session

    def is_session_active(self) -> bool:
        return self.active_session is not None

    def get_session_stats(self) -> Dict[str, Any]:
        """Returns statistics for active or latest session."""
        total_students = len(self.student_repo.get_all(active_only=True))
        if not self.active_session:
            return {
                "active": False,
                "session_id": None,
                "subject": "N/A",
                "class_name": "N/A",
                "present_count": 0,
                "total_students": total_students,
                "attendance_percentage": 0.0
            }

        marked = self.attendance_repo.get_session_attendance(self.active_session.id)
        present_count = len(marked)
        percentage = (present_count / total_students * 100.0) if total_students > 0 else 0.0

        return {
            "active": True,
            "session_id": self.active_session.id,
            "subject": self.active_session.subject,
            "class_name": self.active_session.class_name,
            "present_count": present_count,
            "total_students": total_students,
            "attendance_percentage": percentage
        }
