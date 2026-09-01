import sys
import os
import logging
import cv2

try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except Exception:
    pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from models.download_models import ensure_models_exist
from ui.main_window import MainWindow


def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
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
    logging.info("Starting ikshi Desktop Application...")
    logging.info("==========================================")

def main():
    setup_logging()
    
    # Auto-ensure ONNX models exist (downloads in background if running on fresh machine/Mac/Windows)
    logging.info("Checking face recognition neural models...")
    ensure_models_exist()

    app = QApplication(sys.argv)
    app.setApplicationName("ikshi")
    app.setOrganizationName("ikshi")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

