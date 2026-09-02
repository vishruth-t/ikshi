import sys
import os
import signal
import logging
import cv2

signal.signal(signal.SIGINT, signal.SIG_DFL)

try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except Exception:
    pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from models.download_models import ensure_models_exist
from ui.main_window import MainWindow


def ensure_runtime_dirs():
    """Ensure all required local application directories exist on fresh clone."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for rel_path in [
        "logs",
        "data",
        "data/avatars",
        "data/security_audits",
        "data/sounds",
        "models",
        "models/face_detection",
        "models/sface"
    ]:
        os.makedirs(os.path.join(base_dir, rel_path), exist_ok=True)


def setup_logging():
    ensure_runtime_dirs()
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_file = os.path.join(log_dir, "ikshi.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("==========================================")
    logging.info("Starting IKSHI Desktop Application...")
    logging.info("==========================================")


def main():
    setup_logging()
    
    # Auto-ensure ONNX models exist (downloads with retry & mirrors on fresh clone)
    logging.info("Checking face recognition neural models...")
    models_ready = ensure_models_exist()
    if not models_ready:
        logging.warning("One or more ONNX models could not be verified automatically. Starting app with available resources.")

    # High-DPI multi-monitor awareness for Windows, macOS & Linux
    try:
        if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("IKSHI")
    app.setOrganizationName("IKSHI")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


