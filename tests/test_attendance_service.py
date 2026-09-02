import pytest
from unittest.mock import MagicMock
from database.models import Attendance, Student, AttendanceSession, RecognitionResult
from database.repositories import AttendanceRepository, StudentRepository
from attendance.session_manager import SessionManager
from attendance.attendance_service import AttendanceService

def test_attendance_service_unconfirmed_result():
    att_repo = MagicMock(spec=AttendanceRepository)
    st_repo = MagicMock(spec=StudentRepository)
    sess_mgr = MagicMock(spec=SessionManager)

    service = AttendanceService(att_repo, st_repo, sess_mgr)
    res = RecognitionResult(student_id=1, name="Darshan", confirmed=False)

    success, msg = service.process_recognition(res)
    assert success is False
    assert "Unconfirmed" in msg

def test_attendance_service_no_active_session():
    att_repo = MagicMock(spec=AttendanceRepository)
    st_repo = MagicMock(spec=StudentRepository)
    sess_mgr = MagicMock(spec=SessionManager)

    sess_mgr.get_active_session.return_value = None
    service = AttendanceService(att_repo, st_repo, sess_mgr)
    res = RecognitionResult(student_id=1, name="Darshan", confirmed=True, similarity=0.9)

    success, msg = service.process_recognition(res)
    assert success is False
    assert "No active attendance session" in msg

def test_attendance_service_inactive_student():
    att_repo = MagicMock(spec=AttendanceRepository)
    st_repo = MagicMock(spec=StudentRepository)
    sess_mgr = MagicMock(spec=SessionManager)

    sess_mgr.get_active_session.return_value = AttendanceSession(id=10, subject="Math", class_name="101")
    st_repo.get_by_id.return_value = Student(id=1, name="Darshan", active=False)

    service = AttendanceService(att_repo, st_repo, sess_mgr)
    res = RecognitionResult(student_id=1, name="Darshan", confirmed=True, similarity=0.9)

    success, msg = service.process_recognition(res)
    assert success is False
    assert "inactive" in msg

def test_attendance_service_already_marked():
    att_repo = MagicMock(spec=AttendanceRepository)
    st_repo = MagicMock(spec=StudentRepository)
    sess_mgr = MagicMock(spec=SessionManager)

    sess_mgr.get_active_session.return_value = AttendanceSession(id=10, subject="Math", class_name="101")
    st_repo.get_by_id.return_value = Student(id=1, name="Darshan", active=True)
    att_repo.is_marked.return_value = True

    service = AttendanceService(att_repo, st_repo, sess_mgr)
    res = RecognitionResult(student_id=1, name="Darshan", confirmed=True, similarity=0.9)

    success, msg = service.process_recognition(res)
    assert success is False
    assert "already marked" in msg

def test_attendance_service_success():
    att_repo = MagicMock(spec=AttendanceRepository)
    st_repo = MagicMock(spec=StudentRepository)
    sess_mgr = MagicMock(spec=SessionManager)

    sess_mgr.get_active_session.return_value = AttendanceSession(id=10, subject="Math", class_name="101")
    st_repo.get_by_id.return_value = Student(id=1, student_number="STU001", name="Darshan", active=True)
    att_repo.is_marked.return_value = False
    att_repo.record_attendance.return_value = True

    service = AttendanceService(att_repo, st_repo, sess_mgr)
    res = RecognitionResult(student_id=1, name="Darshan", confirmed=True, similarity=0.9, liveness_passed=True, liveness_score=0.85)

    success, msg = service.process_recognition(res)
    assert success is True
    assert "Attendance marked for Darshan" in msg
    att_repo.record_attendance.assert_called_once()


def test_attendance_service_liveness_failed():
    from config.settings import settings
    settings.enable_ir_liveness = True

    att_repo = MagicMock(spec=AttendanceRepository)
    st_repo = MagicMock(spec=StudentRepository)
    sess_mgr = MagicMock(spec=SessionManager)

    sess_mgr.get_active_session.return_value = AttendanceSession(id=10, subject="Math", class_name="101")
    st_repo.get_by_id.return_value = Student(id=1, student_number="STU001", name="Darshan", active=True)

    service = AttendanceService(att_repo, st_repo, sess_mgr)
    res = RecognitionResult(
        student_id=1,
        name="Darshan",
        confirmed=True,
        similarity=0.9,
        liveness_passed=False,
        liveness_score=0.22,
        liveness_message="Spoof detected: Flat 2D Texture"
    )

    success, msg = service.process_recognition(res)
    assert success is False
    assert "Liveness check failed" in msg
    att_repo.record_attendance.assert_not_called()
    settings.enable_ir_liveness = False

