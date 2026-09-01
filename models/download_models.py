import os
import urllib.request
import logging

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
YUNET_PATH = os.path.join(MODELS_DIR, "face_detection", "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "sface", "face_recognition_sface_2021dec.onnx")

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

def download_file(url: str, target_path: str):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    if os.path.exists(target_path):
        logger.info(f"Model already exists at {target_path}")
        return True
    logger.info(f"Downloading model from {url} to {target_path}...")
    try:
        urllib.request.urlretrieve(url, target_path)
        logger.info(f"Successfully downloaded {target_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download model from {url}: {e}")
        return False

def ensure_models_exist() -> bool:
    """Download required ONNX models if not present."""
    yunet_ok = download_file(YUNET_URL, YUNET_PATH)
    sface_ok = download_file(SFACE_URL, SFACE_PATH)
    return yunet_ok and sface_ok

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Downloading required OpenCV ONNX models...")
    success = ensure_models_exist()
    if success:
        print("All model files are ready!")
    else:
        print("Model download failed. Please check internet connection or download manually.")
