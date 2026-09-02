import os
import urllib.request
import logging

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
YUNET_PATH = os.path.join(MODELS_DIR, "face_detection", "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "sface", "face_recognition_sface_2021dec.onnx")

import ssl

YUNET_MIN_SIZE = 200_000 # ~232 KB
SFACE_MIN_SIZE = 30_000_000 # ~38 MB

YUNET_URLS = [
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
]

SFACE_URLS = [
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
]


def download_file(urls: list, target_path: str, min_size: int = 10000) -> bool:
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    if os.path.exists(target_path) and os.path.getsize(target_path) >= min_size:
        logger.info(f"Model already exists at {target_path} ({os.path.getsize(target_path)} bytes)")
        return True

    # If partial/corrupt file exists, clean it up
    if os.path.exists(target_path) and os.path.getsize(target_path) < min_size:
        try:
            os.remove(target_path)
        except Exception:
            pass

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for url in urls:
        logger.info(f"Downloading model from {url} to {target_path}...")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=30.0) as response, open(target_path, "wb") as out_file:
                chunk_size = 64 * 1024
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)

            if os.path.exists(target_path) and os.path.getsize(target_path) >= min_size:
                logger.info(f"Successfully downloaded {target_path} ({os.path.getsize(target_path)} bytes)")
                return True
            else:
                logger.warning(f"Downloaded file {target_path} is smaller than expected min_size {min_size}.")
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {e}")

    return False


def ensure_models_exist() -> bool:
    """Download required ONNX models if not present or corrupt."""
    yunet_ok = download_file(YUNET_URLS, YUNET_PATH, YUNET_MIN_SIZE)
    sface_ok = download_file(SFACE_URLS, SFACE_PATH, SFACE_MIN_SIZE)
    return yunet_ok and sface_ok

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Downloading required OpenCV ONNX models...")
    success = ensure_models_exist()
    if success:
        print("All model files are ready!")
    else:
        print("Model download failed. Please check internet connection or download manually.")
