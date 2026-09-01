import pytest
import numpy as np
from unittest.mock import MagicMock
from database.repositories import FaceEmbeddingRepository
from recognition.sface_model import SFaceRecognizer
from recognition.matcher import FaceMatcher
from database.models import RecognitionResult

def test_face_matcher_cosine():
    emb_repo = MagicMock(spec=FaceEmbeddingRepository)
    sface = MagicMock(spec=SFaceRecognizer)

    target_vec = np.ones((1, 128), dtype=np.float32)
    registered_vec = np.ones((1, 128), dtype=np.float32)

    # Mock DB embeddings return (student_id, student_number, name, vec)
    emb_repo.get_all_embeddings.return_value = [(10, "STU10", "Darshan", registered_vec)]
    sface.match.return_value = 0.92

    matcher = FaceMatcher(emb_repo, sface)
    result = matcher.find_best_match(target_vec, threshold=0.70)

    assert result.student_id == 10
    assert result.name == "Darshan"
    assert result.similarity == 0.92

def test_face_matcher_below_threshold():
    emb_repo = MagicMock(spec=FaceEmbeddingRepository)
    sface = MagicMock(spec=SFaceRecognizer)

    target_vec = np.ones((1, 128), dtype=np.float32)
    registered_vec = np.zeros((1, 128), dtype=np.float32)

    emb_repo.get_all_embeddings.return_value = [(10, "STU10", "Darshan", registered_vec)]
    sface.match.return_value = 0.45 # Below 0.70 threshold

    matcher = FaceMatcher(emb_repo, sface)
    result = matcher.find_best_match(target_vec, threshold=0.70)

    assert result.student_id is None
    assert result.name == "Unknown"
    assert result.similarity == 0.45
