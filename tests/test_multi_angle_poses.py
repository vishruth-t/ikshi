import os
import tempfile
import numpy as np
import pytest
from database.connection import DatabaseConnection
from database.models import Student, FaceEmbedding, RecognitionResult
from database.repositories import StudentRepository, FaceEmbeddingRepository
from vision.face_detector import FaceDetector
from recognition.sface_model import SFaceRecognizer
from recognition.matcher import FaceMatcher, POSE_DISPLAY_NAMES
from enrollment.enrollment_service import EnrollmentService
from ui.pages.registration import estimate_face_pose, REGISTRATION_POSES

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseConnection(path)
    yield db
    if os.path.exists(path):
        os.remove(path)

def test_estimate_face_pose_yaw_and_pitch():
    # 1. Frontal landmarks
    lm_center = np.array([
        [100, 100], # Right eye
        [160, 100], # Left eye
        [130, 125], # Nose
        [110, 150], # Right mouth
        [150, 150]  # Left mouth
    ])
    yaw, pitch, desc = estimate_face_pose(lm_center)
    assert abs(yaw) < 0.10
    assert desc == "Frontal Center"

    # 2. Turn Left landmarks
    lm_left = np.array([
        [115, 100], # Right eye
        [160, 100], # Left eye
        [145, 125], # Nose closer to left image edge (turned left)
        [125, 150],
        [155, 150]
    ])
    yaw, pitch, desc = estimate_face_pose(lm_left)
    assert yaw > 0.10
    assert desc == "Facing Left"

    # 3. Turn Right landmarks
    lm_right = np.array([
        [100, 100], # Right eye
        [145, 100], # Left eye
        [115, 125], # Nose closer to right image edge (turned right)
        [105, 150],
        [135, 150]
    ])
    yaw, pitch, desc = estimate_face_pose(lm_right)
    assert yaw < -0.10
    assert desc == "Facing Right"

    # 4. Chin Up landmarks
    lm_up = np.array([
        [100, 100],
        [160, 100],
        [130, 115], # Nose higher up towards eyes
        [110, 150],
        [150, 150]
    ])
    yaw, pitch, desc = estimate_face_pose(lm_up)
    assert pitch < 0.44
    assert desc == "Tilted Up"

def test_multi_angle_enrollment_and_matching(temp_db):
    st_repo = StudentRepository(temp_db)
    emb_repo = FaceEmbeddingRepository(temp_db)
    det = FaceDetector()
    rec = SFaceRecognizer()
    enroll_svc = EnrollmentService(st_repo, emb_repo, det, rec)

    student = Student(student_number="STU-777", name="Jane Doe", department="Computer Science & Engineering", year="2025–26")
    
    # 5 orthogonal synthetic feature vectors for 5 distinct angles
    v_frontal = np.zeros(128, dtype=np.float32)
    v_frontal[0] = 1.0
    v_left = np.zeros(128, dtype=np.float32)
    v_left[1] = 1.0
    v_right = np.zeros(128, dtype=np.float32)
    v_right[2] = 1.0
    v_up = np.zeros(128, dtype=np.float32)
    v_up[3] = 1.0
    v_smile = np.zeros(128, dtype=np.float32)
    v_smile[4] = 1.0

    features = [v_frontal, v_left, v_right, v_up, v_smile]
    pose_tags = ["center", "left", "right", "up", "smile_down"]

    success, msg = enroll_svc.register_student_with_embeddings(
        student,
        features=features,
        pose_tags=pose_tags
    )
    assert success is True

    # Verify embeddings stored in DB
    all_emb = emb_repo.get_all_embeddings(model_name="SFace")
    assert len(all_emb) == 5
    tags_in_db = [item[4] for item in all_emb]
    assert tags_in_db == ["center", "left", "right", "up", "smile_down"]

    # Match against matcher
    matcher = FaceMatcher(emb_repo, rec)
    
    # Probe with Left angle vector
    res_left = matcher.find_best_match(v_left, threshold=0.36)
    assert res_left.name == "Jane Doe"
    assert res_left.matched_pose == "Left Angle"
    assert res_left.similarity > 0.99

    # Probe with Up angle vector
    res_up = matcher.find_best_match(v_up, threshold=0.36)
    assert res_up.name == "Jane Doe"
    assert res_up.matched_pose == "Upward Tilt"
    assert res_up.similarity > 0.99

    # Probe with Frontal vector
    res_front = matcher.find_best_match(v_frontal, threshold=0.36)
    assert res_front.name == "Jane Doe"
    assert res_front.matched_pose == "Frontal"
