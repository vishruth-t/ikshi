import os
import tempfile
import numpy as np
import pytest
from database.connection import DatabaseConnection
from database.models import Student, AttendanceSession, Attendance
from database.repositories import StudentRepository, SessionRepository, AttendanceRepository
from reports.exporter import AttendanceExporter
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS
from vision.image_utils import validate_face_sample

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseConnection(path)
    yield db
    if os.path.exists(path):
        os.remove(path)

def test_centralized_constants_integrity():
    assert len(DEFAULT_ACADEMIC_YEARS) >= 4
    assert "2025–26" in DEFAULT_ACADEMIC_YEARS
    assert "Computer Science & Engineering" in DEFAULT_DEPARTMENTS
    assert len(DEFAULT_DEPARTMENTS) >= 6

def test_dynamic_face_capture_prompts():
    # Blank frame -> lighting check fails or no face
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    valid, title, sub = validate_face_sample(blank, (0, 0, 0, 0), 0)
    assert valid is False
    assert title == "No face detected"

    # Multiple faces
    valid, title, sub = validate_face_sample(blank, (100, 100, 150, 150), 2)
    assert valid is False
    assert title == "Multiple faces detected"

    # Too small / far
    valid, title, sub = validate_face_sample(blank, (100, 100, 40, 40), 1)
    assert valid is False
    assert title == "Move closer"

    # Off center
    valid, title, sub = validate_face_sample(blank, (550, 100, 120, 120), 1)
    assert valid is False
    assert title == "Center your face"

def test_report_export_with_academic_year_and_department(temp_db):
    st_repo = StudentRepository(temp_db)
    sess_repo = SessionRepository(temp_db)
    att_repo = AttendanceRepository(temp_db)

    s1 = st_repo.create(Student(
        student_number="CS-001",
        name="Alice",
        department="Computer Science & Engineering",
        year="2025–26"
    ))
    s2 = st_repo.create(Student(
        student_number="ME-002",
        name="Bob",
        department="Mechanical Engineering",
        year="2024–25"
    ))

    sess = sess_repo.create_session(AttendanceSession(
        date="2026-09-01",
        subject="AI Lab",
        class_name="CS-A"
    ))

    att_repo.record_attendance(Attendance(
        session_id=sess.id,
        student_id=s1.id,
        status="Present",
        similarity=0.94
    ))
    att_repo.record_attendance(Attendance(
        session_id=sess.id,
        student_id=s2.id,
        status="Present",
        similarity=0.89
    ))

    # Filter only CS dept
    cs_data = att_repo.get_report_data(department="Computer Science & Engineering")
    assert len(cs_data) == 1
    assert cs_data[0]["name"] == "Alice"
    assert cs_data[0]["year"] == "2025–26"

    # Filter only 2024–25 year
    y_data = att_repo.get_report_data(year="2024–25")
    assert len(y_data) == 1
    assert y_data[0]["name"] == "Bob"

    # Export to CSV
    fd, export_path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        success = AttendanceExporter.export_to_csv(export_path, cs_data)
        assert success is True
        with open(export_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            assert "Alice" in content
            assert "Computer Science & Engineering" in content
            assert "2025–26" in content
            assert "Bob" not in content
    finally:
        if os.path.exists(export_path):
            os.remove(export_path)

def test_camera_worker_helper_functions():
    from ui.workers.camera_worker import CameraWorker, test_capture_device, open_video_capture
    
    worker = CameraWorker("0")
    assert worker.camera_source == 0

    worker_net = CameraWorker("192.168.1.50:8080")
    assert worker_net.camera_source == "http://192.168.1.50:8080/video"

    # Test invalid string URL handling
    ok, cap = test_capture_device("http://127.0.0.1:99999/nonexistent")
    assert ok is False
    assert cap is None

