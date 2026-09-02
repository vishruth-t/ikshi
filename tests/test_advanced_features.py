import os
import pytest
import numpy as np
from database.connection import DatabaseConnection
from database.repositories import SecurityAuditRepository, StudentRepository, FaceEmbeddingRepository
from database.models import Student, FaceEmbedding
from reports.exporter import AttendanceExporter
from recognition.matcher import FaceMatcher
from recognition.sface_model import SFaceRecognizer
from ui.utils.sound_effects import ensure_chime_sound_exists

@pytest.fixture
def test_db(tmp_path):
    db_file = os.path.join(tmp_path, "test_advanced.db")
    return DatabaseConnection(db_file)

def test_security_audit_repository(test_db):
    repo = SecurityAuditRepository(test_db)

    # 1. Log audit
    audit_id = repo.log_audit(
        reason="Phone bezel detected (38% screen edge)",
        matched_student_id=None,
        matched_name="Spoof Attempt",
        liveness_score=0.15,
        texture_score=0.20,
        reflectance_score=0.10,
        entropy_score=0.45,
        motion_score=0.80,
        snapshot_path="/tmp/spoof_rgb.jpg",
        ir_snapshot_path="/tmp/spoof_ir.jpg"
    )
    assert audit_id > 0

    # 2. Get audits
    audits = repo.get_all_audits()
    assert len(audits) == 1
    assert audits[0]["reason"] == "Phone bezel detected (38% screen edge)"
    assert audits[0]["liveness_score"] == 0.15

    # 3. Clear audits
    cleared = repo.clear_audits()
    assert cleared == 1
    assert len(repo.get_all_audits()) == 0

def test_vectorized_face_matcher(test_db):
    stu_repo = StudentRepository(test_db)
    emb_repo = FaceEmbeddingRepository(test_db)

    stu = Student(student_number="S100", name="Bob Martin", department="CSE", year="4th Year")
    created_stu = stu_repo.create(stu)
    stu_id = created_stu.id

    # Enroll normalized vector
    v = np.random.randn(1, 128).astype(np.float32)
    v /= np.linalg.norm(v)
    emb_repo.add_embedding(FaceEmbedding(student_id=stu_id, embedding=v, model_name="SFace"))

    sface = SFaceRecognizer()
    matcher = FaceMatcher(emb_repo, sface)

    # Best match with identical vector
    res = matcher.find_best_match(v, threshold=0.70)
    assert res.student_id == stu_id
    assert res.student_number == "S100"
    assert res.similarity > 0.99

def test_exporters(tmp_path):
    csv_file = os.path.join(tmp_path, "out.csv")
    html_file = os.path.join(tmp_path, "out.html")
    xls_file = os.path.join(tmp_path, "out.xls")

    data = [{
        "date": "2026-09-02",
        "student_number": "ST-999",
        "name": "Test Student",
        "department": "IT",
        "year": "2nd Year",
        "subject": "Cybersecurity",
        "class_name": "Section B",
        "marked_at": "2026-09-02 10:15:00",
        "status": "Present",
        "similarity": 0.94,
        "liveness_score": 0.85
    }]

    assert AttendanceExporter.export_to_csv(csv_file, data)
    assert os.path.exists(csv_file)

    assert AttendanceExporter.export_to_html(html_file, data)
    assert os.path.exists(html_file)
    with open(html_file, "r") as f:
        content = f.read()
        assert "Test Student" in content
        assert "Cybersecurity" in content

    assert AttendanceExporter.export_to_excel_xml(xls_file, data)
    assert os.path.exists(xls_file)

def test_sound_chime_generation():
    chime_path = ensure_chime_sound_exists()
    assert os.path.exists(chime_path)
    assert os.path.getsize(chime_path) > 1000
