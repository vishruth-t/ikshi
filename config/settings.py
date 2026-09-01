import os
import json
import logging
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "app_config.json")

@dataclass
class AppSettings:
    camera_index: int = 0
    camera_fps: int = 30
    camera_width: int = 1280
    camera_height: int = 720
    
    # Model paths
    detection_model_path: str = os.path.join(BASE_DIR, "models", "face_detection", "face_detection_yunet_2023mar.onnx")
    recognition_model_path: str = os.path.join(BASE_DIR, "models", "sface", "face_recognition_sface_2021dec.onnx")
    
    # Recognition parameters
    similarity_metric: str = "cosine" # "cosine" or "l2"
    recognition_threshold: float = 0.70 # Default threshold for cosine similarity
    confirmation_frames: int = 3 # N consecutive frames for temporal stability
    
    # Database
    db_path: str = os.path.join(BASE_DIR, "data", "attendance.db")
    
    # Enrollment Quality Checks
    min_face_size: int = 60 # minimum width/height in pixels
    blur_threshold: float = 80.0 # Laplacian variance minimum
    
    def save(self, filepath: str = CONFIG_PATH):
        """Save settings to JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = asdict(self)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Saved application settings to {filepath}")

    @classmethod
    def load(cls, filepath: str = CONFIG_PATH) -> "AppSettings":
        """Load settings from JSON file if exists, else return defaults."""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                settings = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
                logger.info(f"Loaded settings from {filepath}")
                return settings
            except Exception as e:
                logger.error(f"Failed to load settings from {filepath}: {e}, using defaults.")
        return cls()

# Global settings instance
settings = AppSettings.load()
