import numpy as np
import logging
from typing import List, Tuple, Optional
from database.repositories import StudentRepository, FaceEmbeddingRepository
from database.models import Student, FaceEmbedding
from vision.face_detector import FaceDetector, DetectedFace
from vision.face_aligner import align_and_crop_face
from vision.image_utils import validate_face_sample
from recognition.sface_model import SFaceRecognizer
from config.settings import settings

logger = logging.getLogger(__name__)

class EnrollmentService:
    def __init__(
        self,
        student_repo: StudentRepository,
        embedding_repo: FaceEmbeddingRepository,
        detector: FaceDetector,
        sface: SFaceRecognizer
    ):
        self.student_repo = student_repo
        self.embedding_repo = embedding_repo
        self.detector = detector
        self.sface = sface

    def process_sample(self, frame: np.ndarray) -> Tuple[bool, str, Optional[np.ndarray]]:
        """
        Validate single frame sample, detect face, align/crop face, and extract feature vector.
        Returns: (success: bool, feedback_message: str, feature_vector: Optional[np.ndarray])
        """
        if frame is None or not self.detector.is_loaded() or not self.sface.is_loaded():
            return False, "Camera feed or recognition model not ready.", None

        faces = self.detector.detect(frame)
        is_valid, title, subtitle = validate_face_sample(frame, faces[0].bbox if faces else (0,0,0,0), len(faces))
        if not is_valid:
            feedback = f"{title}: {subtitle}" if subtitle else title
            return False, feedback, None

        detected_face = faces[0]
        aligned_crop = self.sface.align_crop(frame, detected_face.raw_face_data)
        if aligned_crop is None:
            return False, "Failed to align face sample.", None

        feature = self.sface.extract_feature(aligned_crop)
        if feature is None:
            return False, "Failed to extract facial data.", None

        return True, "Face captured successfully", feature


    def register_student_with_embeddings(self, student: Student, features: List[np.ndarray]) -> Tuple[bool, str]:
        """
        Save student details and list of sample face embeddings to database.
        """
        if not features:
            return False, "No valid face samples provided."

        existing = self.student_repo.get_by_number(student.student_number)
        if existing:
            return False, f"Student ID '{student.student_number}' already registered."

        try:
            created_student = self.student_repo.create(student)
            for vec in features:
                emb = FaceEmbedding(
                    student_id=created_student.id,
                    embedding=vec,
                    model_name="SFace",
                    model_version="2021dec",
                    metric=settings.similarity_metric
                )
                self.embedding_repo.add_embedding(emb)

            logger.info(f"Successfully registered student '{student.name}' with {len(features)} embeddings.")
            return True, f"Student '{student.name}' successfully enrolled!"
        except Exception as e:
            logger.error(f"Failed to register student: {e}")
            return False, f"Database error: {e}"

    def re_enroll_student_embeddings(self, student_id: int, features: List[np.ndarray]) -> Tuple[bool, str]:
        """
        Replace existing face embeddings with new sample features for a registered student.
        """
        if not features:
            return False, "No valid face samples provided."

        student = self.student_repo.get_by_id(student_id)
        if not student:
            return False, f"Student ID '{student_id}' not found."

        try:
            self.embedding_repo.delete_embeddings_for_student(student_id)
            for vec in features:
                emb = FaceEmbedding(
                    student_id=student_id,
                    embedding=vec,
                    model_name="SFace",
                    model_version="2021dec",
                    metric=settings.similarity_metric
                )
                self.embedding_repo.add_embedding(emb)

            logger.info(f"Successfully re-enrolled student '{student.name}' (ID: {student_id}) with {len(features)} embeddings.")
            return True, f"Face features re-enrolled successfully for '{student.name}'!"
        except Exception as e:
            logger.error(f"Failed to re-enroll student: {e}")
            return False, f"Database error: {e}"

