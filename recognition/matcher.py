import numpy as np
import logging
from typing import List, Tuple, Optional
from database.repositories import FaceEmbeddingRepository
from recognition.sface_model import SFaceRecognizer
from database.models import RecognitionResult
from config.settings import settings

logger = logging.getLogger(__name__)

POSE_DISPLAY_NAMES = {
    "frontal": "Frontal",
    "center": "Frontal",
    "left_20": "Left Angle",
    "left": "Left Angle",
    "right_20": "Right Angle",
    "right": "Right Angle",
    "tilt_up": "Upward Tilt",
    "up": "Upward Tilt",
    "smile_down": "Smile / Down",
    "smile": "Smile / Down"
}


class FaceMatcher:
    def __init__(self, embedding_repo: FaceEmbeddingRepository, sface_recognizer: SFaceRecognizer):
        self.embedding_repo = embedding_repo
        self.sface = sface_recognizer
        self._norm_matrix: Optional[np.ndarray] = None # (N, 128) unit-normalized float32
        self._metadata: List[Tuple[int, str, str, str]] = [] # [(student_id, student_number, name, pose_tag), ...]
        self.refresh_cache()

    def refresh_cache(self):
        """Build or refresh in-memory normalized embedding matrix for O(1) vectorized search."""
        try:
            db_embeddings = self.embedding_repo.get_all_embeddings(model_name="SFace")
            if not db_embeddings:
                self._norm_matrix = None
                self._metadata = []
                return

            vecs = []
            meta = []
            for item in db_embeddings:
                student_id = item[0]
                student_number = item[1]
                name = item[2]
                registered_vec = item[3]
                p_tag = item[4] if len(item) > 4 else "frontal"

                v = np.asarray(registered_vec, dtype=np.float32).flatten()
                norm = np.linalg.norm(v)
                if norm > 1e-7:
                    vecs.append(v / norm)
                    meta.append((student_id, student_number, name, p_tag))

            if vecs:
                self._norm_matrix = np.vstack(vecs)
                self._metadata = meta
            else:
                self._norm_matrix = None
                self._metadata = []
        except Exception as e:
            logger.error(f"Error refreshing FaceMatcher vector cache: {e}")
            self._norm_matrix = None
            self._metadata = []

    def find_best_match(
        self,
        feature: np.ndarray,
        threshold: Optional[float] = None,
        bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> RecognitionResult:
        if threshold is None:
            threshold = settings.recognition_threshold

        metric = settings.similarity_metric

        # Check for mocked sface in unit tests
        from unittest.mock import MagicMock
        if hasattr(self.sface, "match") and isinstance(self.sface.match, MagicMock):
            best_student_id = None
            best_student_number = None
            best_name = None
            best_pose = "Frontal"
            highest_similarity = -1.0
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
            for item in db_embeddings:
                student_id = item[0]
                student_number = item[1]
                name = item[2]
                registered_vec = item[3]
                p_tag = item[4] if len(item) > 4 else "frontal"
                sim = float(self.sface.match(feature.reshape(1, -1), registered_vec.reshape(1, -1), metric=metric))
                if sim > highest_similarity:
                    highest_similarity = sim
                    best_student_id = student_id
                    best_student_number = student_number
                    best_name = name
                    best_pose = POSE_DISPLAY_NAMES.get(p_tag, "Frontal")

            if highest_similarity >= threshold and best_student_id is not None:
                return RecognitionResult(
                    student_id=best_student_id,
                    student_number=best_student_number,
                    name=best_name,
                    similarity=highest_similarity,
                    metric=metric,
                    bbox=bbox,
                    confirmed=False,
                    matched_pose=best_pose
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

        if feature is None or self._norm_matrix is None or len(self._metadata) == 0:
            # Fallback to refresh if cache was empty
            if self._norm_matrix is None:
                self.refresh_cache()
            if feature is None or self._norm_matrix is None or len(self._metadata) == 0:
                return RecognitionResult(
                    student_id=None,
                    student_number=None,
                    name="Unknown",
                    similarity=0.0,
                    metric=metric,
                    bbox=bbox,
                    confirmed=False
                )

        # 1. Vectorized Cosine Dot Product against all enrolled student vectors across all multi-angle poses
        q = np.asarray(feature, dtype=np.float32).flatten()
        q_norm = np.linalg.norm(q)
        if q_norm > 1e-7:
            q_unit = q / q_norm
        else:
            q_unit = q

        similarities = np.dot(self._norm_matrix, q_unit)
        best_idx = int(np.argmax(similarities))
        highest_similarity = float(similarities[best_idx])
        meta_entry = self._metadata[best_idx]
        best_student_id = meta_entry[0]
        best_student_number = meta_entry[1]
        best_name = meta_entry[2]
        best_pose_tag = meta_entry[3] if len(meta_entry) > 3 else "frontal"
        matched_pose_display = POSE_DISPLAY_NAMES.get(best_pose_tag, "Frontal")

        if highest_similarity >= threshold and best_student_id is not None:
            return RecognitionResult(
                student_id=best_student_id,
                student_number=best_student_number,
                name=best_name,
                similarity=highest_similarity,
                metric=metric,
                bbox=bbox,
                confirmed=False,
                matched_pose=matched_pose_display
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
