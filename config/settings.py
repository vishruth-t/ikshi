import os
import json
import logging
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "app_config.json")

def _resolve_portable_path(path_str: str, default_relative: str) -> str:
    """Resolve a path portably across macOS, Windows, and Linux."""
    if not path_str:
        return os.path.join(BASE_DIR, default_relative)
    # If it's an existing absolute path on this specific OS
    if os.path.isabs(path_str) and os.path.exists(path_str):
        return path_str
    # If it's a relative path from BASE_DIR
    if not os.path.isabs(path_str):
        return os.path.normpath(os.path.join(BASE_DIR, path_str))
    # If it's an absolute path from another machine (e.g. /home/da/.. on Mac), fallback to current repo BASE_DIR
    return os.path.normpath(os.path.join(BASE_DIR, default_relative))

@dataclass
class AppSettings:
    camera_index: int = 0
    camera_source: str = "0" # Can be device index ("0", "1") or Network URL ("http://192.168.1.100:8080/video", "rtsp://...")
    camera_fps: int = 30
    camera_width: int = 1280
    camera_height: int = 720
    
    # Model paths
    detection_model_path: str = os.path.join(BASE_DIR, "models", "face_detection", "face_detection_yunet_2023mar.onnx")
    recognition_model_path: str = os.path.join(BASE_DIR, "models", "sface", "face_recognition_sface_2021dec.onnx")
    
    # Recognition parameters
    similarity_metric: str = "cosine" # "cosine" or "l2"
    recognition_threshold: float = 0.363 # Recommended OpenCV SFace threshold for cosine similarity
    confirmation_frames: int = 3 # N consecutive frames for temporal stability
    
    # Database
    db_path: str = os.path.join(BASE_DIR, "data", "attendance.db")
    
    # Enrollment Quality Checks
    min_face_size: int = 60 # minimum width/height in pixels
    blur_threshold: float = 35.0 # Laplacian variance minimum

    def get_capture_source(self):
        """Returns int device index or str stream URL for OpenCV VideoCapture."""
        src = str(self.camera_source).strip() if self.camera_source else str(self.camera_index)
        if src.isdigit():
            return int(src)
        return src

    def save(self, filepath: str = CONFIG_PATH):
        """Save settings to JSON file with relative portable paths."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = asdict(self)
        # Store paths portably (relative to BASE_DIR where applicable)
        for key in ["detection_model_path", "recognition_model_path", "db_path"]:
            if key in data and data[key]:
                try:
                    rel = os.path.relpath(data[key], BASE_DIR)
                    if not rel.startswith(".."):
                        data[key] = rel
                except ValueError:
                    pass
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Saved application settings to {filepath}")

    @classmethod
    def load(cls, filepath: str = CONFIG_PATH) -> "AppSettings":
        """Load settings from JSON file if exists, resolving paths portably for any OS."""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Portably resolve paths for current OS
                if "detection_model_path" in data:
                    data["detection_model_path"] = _resolve_portable_path(
                        data["detection_model_path"],
                        os.path.join("models", "face_detection", "face_detection_yunet_2023mar.onnx")
                    )
                if "recognition_model_path" in data:
                    data["recognition_model_path"] = _resolve_portable_path(
                        data["recognition_model_path"],
                        os.path.join("models", "sface", "face_recognition_sface_2021dec.onnx")
                    )
                if "db_path" in data:
                    data["db_path"] = _resolve_portable_path(
                        data["db_path"],
                        os.path.join("data", "attendance.db")
                    )

                settings = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
                logger.info(f"Loaded settings from {filepath}")
                return settings
            except Exception as e:
                logger.error(f"Failed to load settings from {filepath}: {e}, using defaults.")
        return cls()

# Global settings instance
settings = AppSettings.load()

