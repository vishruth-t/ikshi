import numpy as np
from recognition.sface_model import SFaceRecognizer

def align_and_crop_face(image: np.ndarray, face_data: np.ndarray, sface: SFaceRecognizer) -> np.ndarray:
    """Helper wrapper for face alignment and cropping."""
    return sface.align_crop(image, face_data)
