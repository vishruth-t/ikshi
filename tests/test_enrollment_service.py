import pytest
import numpy as np
from unittest.mock import MagicMock
from database.models import Student, FaceEmbedding
from database.repositories import StudentRepository, FaceEmbeddingRepository
from enrollment.enrollment_service import EnrollmentService
from vision.face_detector import FaceDetector, DetectedFace
from recognition.sface_model import SFaceRecognizer

def test_enrollment_register_success():
    st_repo = MagicMock(spec=StudentRepository)
    emb_repo = MagicMock(spec=FaceEmbeddingRepository)
    detector = MagicMock(spec=FaceDetector)
    sface = MagicMock(spec=SFaceRecognizer)

    st_repo.get_by_number.return_value = None
    created_mock = Student(id=1, student_number="STU100", name="Test Student")
    st_repo.create.return_value = created_mock

    service = EnrollmentService(st_repo, emb_repo, detector, sface)
    features = [np.random.randn(128).astype(np.float32) for _ in range(5)]

    success, msg = service.register_student_with_embeddings(created_mock, features)
    assert success is True
    assert "successfully enrolled" in msg
    assert emb_repo.add_embedding.call_count == 5

def test_enrollment_register_duplicate_student_number():
    st_repo = MagicMock(spec=StudentRepository)
    emb_repo = MagicMock(spec=FaceEmbeddingRepository)
    detector = MagicMock(spec=FaceDetector)
    sface = MagicMock(spec=SFaceRecognizer)

    st_repo.get_by_number.return_value = Student(id=1, student_number="STU100", name="Existing Student")

    service = EnrollmentService(st_repo, emb_repo, detector, sface)
    student = Student(student_number="STU100", name="Duplicate Student")
    features = [np.random.randn(128).astype(np.float32)]

    success, msg = service.register_student_with_embeddings(student, features)
    assert success is False
    assert "already registered" in msg

def test_enrollment_re_enroll_success():
    st_repo = MagicMock(spec=StudentRepository)
    emb_repo = MagicMock(spec=FaceEmbeddingRepository)
    detector = MagicMock(spec=FaceDetector)
    sface = MagicMock(spec=SFaceRecognizer)

    st_repo.get_by_id.return_value = Student(id=5, student_number="STU105", name="Re-enroll Student")

    service = EnrollmentService(st_repo, emb_repo, detector, sface)
    features = [np.random.randn(128).astype(np.float32) for _ in range(5)]

    success, msg = service.re_enroll_student_embeddings(5, features)
    assert success is True
    emb_repo.delete_embeddings_for_student.assert_called_once_with(5)
    assert emb_repo.add_embedding.call_count == 5

def test_enrollment_re_enroll_nonexistent_student():
    st_repo = MagicMock(spec=StudentRepository)
    emb_repo = MagicMock(spec=FaceEmbeddingRepository)
    detector = MagicMock(spec=FaceDetector)
    sface = MagicMock(spec=SFaceRecognizer)

    st_repo.get_by_id.return_value = None

    service = EnrollmentService(st_repo, emb_repo, detector, sface)
    features = [np.random.randn(128).astype(np.float32)]

    success, msg = service.re_enroll_student_embeddings(999, features)
    assert success is False
    assert "not found" in msg


def test_enrollment_register_dual_rgb_and_ir():
    st_repo = MagicMock(spec=StudentRepository)
    emb_repo = MagicMock(spec=FaceEmbeddingRepository)
    detector = MagicMock(spec=FaceDetector)
    sface = MagicMock(spec=SFaceRecognizer)

    st_repo.get_by_number.return_value = None
    created_mock = Student(id=2, student_number="STU200", name="Dual Sensor Student")
    st_repo.create.return_value = created_mock

    service = EnrollmentService(st_repo, emb_repo, detector, sface)
    rgb_features = [np.random.randn(128).astype(np.float32) for _ in range(5)]
    ir_features = [np.random.randn(128).astype(np.float32) for _ in range(5)]

    success, msg = service.register_student_with_embeddings(
        created_mock,
        features=rgb_features,
        features_ir=ir_features
    )
    assert success is True
    assert "5 RGB, 5 IR" in msg
    # 5 RGB + 5 IR = 10 total embeddings saved
    assert emb_repo.add_embedding.call_count == 10

