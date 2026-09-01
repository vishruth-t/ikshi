import cv2
import time
import numpy as np
import logging
from PySide6.QtCore import QThread, Signal
from config.settings import settings

logger = logging.getLogger(__name__)

class CameraWorker(QThread):
    frame_received = Signal(np.ndarray)
    camera_error = Signal(str)

    def __init__(self, camera_index: int = None):
        super().__init__()
        self.camera_index = camera_index if camera_index is not None else settings.camera_index
        self._running = False
        self._cap = None

    def run(self):
        self._running = True
        self._cap = cv2.VideoCapture(self.camera_index)
        
        if not self._cap.isOpened():
            err_msg = f"Unable to open camera index {self.camera_index}"
            logger.error(err_msg)
            self.camera_error.emit(err_msg)
            
            # Generate fallback standby frame loop if physical camera unavailable
            blank_frame = self._create_placeholder_frame("Camera Unavailable - Check Connection")
            while self._running:
                self.frame_received.emit(blank_frame)
                self.msleep(100)
            return

        logger.info(f"CameraWorker started on camera index {self.camera_index}")
        target_delay_ms = int(1000 / settings.camera_fps)

        while self._running:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                self.frame_received.emit(frame)
            else:
                self.camera_error.emit("Failed to grab frame from camera.")
                fallback = self._create_placeholder_frame("Camera Frame Read Failed")
                self.frame_received.emit(fallback)
                self.msleep(200)

            self.msleep(target_delay_ms)

        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info("CameraWorker stopped.")

    def stop(self):
        self._running = False
        self.wait(2000)

    def _create_placeholder_frame(self, message: str) -> np.ndarray:
        frame = np.zeros((settings.camera_height, settings.camera_width, 3), dtype=np.uint8)
        # Gradient background
        cv2.rectangle(frame, (0, 0), (settings.camera_width, settings.camera_height), (35, 30, 30), -1)
        cv2.putText(frame, message, (100, settings.camera_height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (100, 100, 255), 2)
        cv2.putText(frame, "FaceAttend System Standby", (100, settings.camera_height // 2 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        return frame
