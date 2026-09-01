import os
import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)

class SFaceRecognizer:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.recognition_model_path
        self.recognizer = None
        self._init_model()

    def _init_model(self):
        if not os.path.exists(self.model_path):
            logger.error(f"SFace model not found at {self.model_path}")
            return
        
        try:
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=self.model_path,
                config="",
                backend_id=0,
                target_id=0
            )
            logger.info(f"Initialized OpenCV SFace FaceRecognizerSF from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load SFace FaceRecognizerSF model: {e}")
            self.recognizer = None

    def is_loaded(self) -> bool:
        return self.recognizer is not None

    def align_crop(self, image: np.ndarray, face_data: np.ndarray) -> Optional[np.ndarray]:
        """
        Align and crop face from image using detected face landmarks.
        Returns 112x112 aligned RGB/BGR face crop.
        """
        if not self.is_loaded() or image is None or face_data is None:
            return None
        try:
            aligned_face = self.recognizer.alignCrop(image, face_data)
            return aligned_face
        except Exception as e:
            logger.error(f"Error during SFace alignCrop: {e}")
            return None

    def extract_feature(self, aligned_face: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract 128-dimensional embedding feature vector from aligned face.
        """
        if not self.is_loaded() or aligned_face is None:
            return None
        try:
            feature = self.recognizer.feature(aligned_face)
            return feature
        except Exception as e:
            logger.error(f"Error during SFace feature extraction: {e}")
            return None

    def match(self, feature1: np.ndarray, feature2: np.ndarray, metric: str = "cosine") -> float:
        """
        Calculate similarity score between two feature vectors.
        Metric: 'cosine' (cv2.FaceRecognizerSF.FR_COSINE = 0) or 'l2' (cv2.FaceRecognizerSF.FR_NORM_L2 = 1).
        """
        if not self.is_loaded() or feature1 is None or feature2 is None:
            return 0.0
        try:
            dis_type = cv2.FaceRecognizerSF.FR_COSINE if metric == "cosine" else cv2.FaceRecognizerSF.FR_NORM_L2
            score = self.recognizer.match(feature1, feature2, dis_type)
            return float(score)
        except Exception as e:
            logger.error(f"Error during SFace feature match: {e}")
            return 0.0
