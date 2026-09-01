import os
import tempfile
import pytest
import numpy as np
from database.connection import DatabaseConnection
from database.models import Student, FaceEmbedding, AttendanceSession, Attendance
from database.repositories import (
    StudentRepository, FaceEmbeddingRepository, SessionRepository, AttendanceRepository
)

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseConnection(path)
    yield db
    if os.path.exists(path):
        os.remove(path)

def test_student_crud(temp_db):
    repo = StudentRepository(temp_db)
    student = Student(student_number="STU001", name="Darshan", department="CS", year="3rd Year")
    created = repo.create(student)
    assert created.id is not None

    fetched = repo.get_by_id(created.id)
    assert fetched.name == "Darshan"
    assert fetched.student_number == "STU001"

    # Update
    fetched.name = "Darshan S"
    repo.update(fetched)
    updated = repo.get_by_id(created.id)
    assert updated.name == "Darshan S"

    # Set active status
    repo.set_active(created.id, False)
    disabled = repo.get_by_id(created.id)
    assert disabled.active is False

def test_embedding_storage(temp_db):
    st_repo = StudentRepository(temp_db)
    emb_repo = FaceEmbeddingRepository(temp_db)

    s = st_repo.create(Student(student_number="STU002", name="Alice", department="IT", year="2nd Year"))
    vec = np.random.randn(128).astype(np.float32)

    emb = FaceEmbedding(student_id=s.id, embedding=vec, model_name="SFace", model_version="2021dec")
    saved = emb_repo.add_embedding(emb)
    assert saved.id is not None

    embeddings = emb_repo.get_all_embeddings()
    assert len(embeddings) == 1
    assert embeddings[0][0] == s.id
    assert embeddings[0][1] == "STU002"
    assert embeddings[0][2] == "Alice"
    assert np.allclose(embeddings[0][3], vec, atol=1e-5)

def test_session_and_attendance_duplicate_prevention(temp_db):
    st_repo = StudentRepository(temp_db)
    sess_repo = SessionRepository(temp_db)
    att_repo = AttendanceRepository(temp_db)

    student = st_repo.create(Student(student_number="STU003", name="Bob", department="ECE", year="1st Year"))
    session = sess_repo.create_session(AttendanceSession(subject="Math", class_name="101"))

    att = Attendance(session_id=session.id, student_id=student.id, status="Present", similarity=0.85)

    # First recording -> success
    first_res = att_repo.record_attendance(att)
    assert first_res is True

    # Duplicate recording -> fail / duplicate ignored
    dup_res = att_repo.record_attendance(att)
    assert dup_res is False

    records = att_repo.get_session_attendance(session.id)
    assert len(records) == 1
    assert records[0]["student_number"] == "STU003"

def test_student_deletion_and_cascade(temp_db):
    st_repo = StudentRepository(temp_db)
    emb_repo = FaceEmbeddingRepository(temp_db)
    sess_repo = SessionRepository(temp_db)
    att_repo = AttendanceRepository(temp_db)

    student = st_repo.create(Student(student_number="STU004", name="Charlie", department="Mech", year="4th Year"))
    emb = FaceEmbedding(student_id=student.id, embedding=np.random.randn(128).astype(np.float32))
    emb_repo.add_embedding(emb)

    session = sess_repo.create_session(AttendanceSession(subject="Physics", class_name="PH-201"))
    att_repo.record_attendance(Attendance(session_id=session.id, student_id=student.id, status="Present", similarity=0.9))

    assert len(emb_repo.get_all_embeddings()) == 1
    assert len(att_repo.get_session_attendance(session.id)) == 1

    # Delete student
    deleted = st_repo.delete(student.id)
    assert deleted is True
    assert st_repo.get_by_id(student.id) is None

    # Embeddings and attendance should be cascaded
    assert len(emb_repo.get_all_embeddings()) == 0
    assert len(att_repo.get_session_attendance(session.id)) == 0

def test_report_data_filtering(temp_db):
    st_repo = StudentRepository(temp_db)
    sess_repo = SessionRepository(temp_db)
    att_repo = AttendanceRepository(temp_db)

    s1 = st_repo.create(Student(student_number="STU005", name="David", department="CS", year="1st Year"))
    s2 = st_repo.create(Student(student_number="STU006", name="Eve", department="EE", year="2nd Year"))

    sess1 = sess_repo.create_session(AttendanceSession(date="2026-09-01", subject="AI", class_name="CS-301"))
    sess2 = sess_repo.create_session(AttendanceSession(date="2026-09-02", subject="Circuits", class_name="EE-201"))

    att_repo.record_attendance(Attendance(session_id=sess1.id, student_id=s1.id, status="Present", similarity=0.95))
    att_repo.record_attendance(Attendance(session_id=sess2.id, student_id=s2.id, status="Present", similarity=0.88))

    # Filter by class
    res_cs = att_repo.get_report_data(class_name="CS-301")
    assert len(res_cs) == 1
    assert res_cs[0]["name"] == "David"

    # Filter by subject
    res_circ = att_repo.get_report_data(subject="Circuits")
    assert len(res_circ) == 1
    assert res_circ[0]["name"] == "Eve"

    # Filter by department
    res_dept = att_repo.get_report_data(department="CS")
    assert len(res_dept) == 1
    assert res_dept[0]["name"] == "David"

    # Filter by academic year
    res_year = att_repo.get_report_data(year="2nd Year")
    assert len(res_year) == 1
    assert res_year[0]["name"] == "Eve"

    # Filter by date range
    res_date = att_repo.get_report_data(start_date="2026-09-02", end_date="2026-09-02")
    assert len(res_date) == 1
    assert res_date[0]["name"] == "Eve"


