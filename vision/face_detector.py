import os
import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class DetectedFace:
    def __init__(self, bbox: Tuple[int, int, int, int], landmarks: np.ndarray, score: float, raw_face_data: np.ndarray):
        self.bbox = bbox # (x, y, w, h)
        self.landmarks = landmarks # 5 facial keypoints
        self.score = score # confidence score
        self.raw_face_data = raw_face_data # row vector from FaceDetectorYN

class FaceDetector:
    def __init__(self, model_path: Optional[str] = None, score_threshold: float = 0.8, nms_threshold: float = 0.3):
        self.model_path = model_path or settings.detection_model_path
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.detector = None
        self.current_input_size = (640, 480)
        self._init_detector()

    def _init_detector(self):
        if not os.path.exists(self.model_path):
            logger.error(f"Face detection model not found at {self.model_path}")
            return
        
        try:
            self.detector = cv2.FaceDetectorYN.create(
                model=self.model_path,
                config="",
                input_size=self.current_input_size,
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=5000,
                backend_id=0,
                target_id=0
            )
            logger.info(f"Initialized YuNet FaceDetectorYN from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load FaceDetectorYN model: {e}")
            self.detector = None

    def is_loaded(self) -> bool:
        return self.detector is not None

    def detect(self, image: np.ndarray) -> List[DetectedFace]:
        if not self.is_loaded() or image is None:
            return []

        h, w = image.shape[:2]
        if (w, h) != self.current_input_size:
            self.current_input_size = (w, h)
            self.detector.setInputSize(self.current_input_size)

        try:
            results, faces = self.detector.detect(image)
            if faces is None or len(faces) == 0:
                return []

            detected_faces = []
            for face in faces:
                bbox = (int(face[0]), int(face[1]), int(face[2]), int(face[3]))
                landmarks = face[4:14].reshape((5, 2))
                score = float(face[14])
                detected_faces.append(DetectedFace(bbox, landmarks, score, face))

            return detected_faces
        except Exception as e:
            logger.error(f"Error during face detection: {e}")
            return []
