import numpy as np
import logging
from typing import List, Tuple, Optional
from database.repositories import FaceEmbeddingRepository
from recognition.sface_model import SFaceRecognizer
from database.models import RecognitionResult
from config.settings import settings

logger = logging.getLogger(__name__)

class FaceMatcher:
    def __init__(self, embedding_repo: FaceEmbeddingRepository, sface_recognizer: SFaceRecognizer):
        self.embedding_repo = embedding_repo
        self.sface = sface_recognizer

    def find_best_match(
        self,
        feature: np.ndarray,
        threshold: Optional[float] = None,
        bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> RecognitionResult:
        if threshold is None:
            threshold = settings.recognition_threshold

        metric = settings.similarity_metric
        db_embeddings = self.embedding_repo.get_all_embeddings()

        if not db_embeddings or feature is None:
            return RecognitionResult(
                student_id=None,
                student_number=None,
                name="Unknown",
                similarity=0.0,
                metric=metric,
                bbox=bbox,
                confirmed=False
            )

        best_student_id = None
        best_student_number = None
        best_name = None
        highest_similarity = -1.0

        for student_id, student_number, name, registered_vec in db_embeddings:
            # Reshape vectors if necessary
            vec1 = feature.reshape(1, -1)
            vec2 = registered_vec.reshape(1, -1)

            similarity = self.sface.match(vec1, vec2, metric=metric)

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_student_id = student_id
                best_student_number = student_number
                best_name = name

        if highest_similarity >= threshold and best_student_id is not None:
            return RecognitionResult(
                student_id=best_student_id,
                student_number=best_student_number,
                name=best_name,
                similarity=highest_similarity,
                metric=metric,
                bbox=bbox,
                confirmed=False
            )

        return RecognitionResult(
            student_id=None,
            student_number=None,
            name="Unknown",
            similarity=highest_similarity if highest_similarity > 0 else 0.0,
            metric=metric,
            bbox=bbox,
            confirmed=False
        )
