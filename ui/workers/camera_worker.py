import cv2
import time
import numpy as np
import logging
from typing import Union
from PySide6.QtCore import QThread, Signal, Slot
from config.settings import settings

logger = logging.getLogger(__name__)

class CameraWorker(QThread):
    frame_received = Signal(np.ndarray)
    camera_error = Signal(str)

    def __init__(self, camera_source: Union[int, str] = None):
        super().__init__()
        self.camera_source = self._parse_source(camera_source if camera_source is not None else settings.get_capture_source())
        self._running = False
        self._cap = None

    def _parse_source(self, src: Union[int, str]) -> Union[int, str]:
        if isinstance(src, str) and src.strip().isdigit():
            return int(src.strip())
        return src

    def run(self):
        self._running = True
        logger.info(f"Opening camera capture source: {self.camera_source}")
        self._cap = cv2.VideoCapture(self.camera_source)
        
        if not self._cap.isOpened():
            err_msg = f"Unable to open camera source: {self.camera_source}"
            logger.error(err_msg)
            self.camera_error.emit(err_msg)
            
            # Generate fallback standby frame loop if camera unavailable
            blank_frame = self._create_placeholder_frame(f"Camera Source Unavailable: {self.camera_source}")
            while self._running:
                self.frame_received.emit(blank_frame)
                self.msleep(100)
            return

        logger.info(f"CameraWorker active on source: {self.camera_source}")
        target_delay_ms = int(1000 / settings.camera_fps)

        while self._running:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                self.frame_received.emit(frame)
            else:
                self.camera_error.emit(f"Failed to grab frame from {self.camera_source}")
                fallback = self._create_placeholder_frame("Camera Frame Read Failed - Reconnecting...")
                self.frame_received.emit(fallback)
                self.msleep(500)
                # Attempt light reconnect if stream dropped
                if self._running and isinstance(self.camera_source, str) and self.camera_source.startswith("http"):
                    if self._cap:
                        self._cap.release()
                    self._cap = cv2.VideoCapture(self.camera_source)

            self.msleep(target_delay_ms)

        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info("CameraWorker stopped.")

    def update_source(self, new_source: Union[int, str]):
        """Restart camera capture on a new device or network stream URL."""
        parsed = self._parse_source(new_source)
        if parsed == self.camera_source and self.isRunning():
            return
        logger.info(f"Switching camera source to: {parsed}")
        self.stop()
        self.camera_source = parsed
        self.start()

    def stop(self):
        self._running = False
        self.wait(2000)

    def _create_placeholder_frame(self, message: str) -> np.ndarray:
        frame = np.zeros((settings.camera_height, settings.camera_width, 3), dtype=np.uint8)
        # Dark stylish background
        cv2.rectangle(frame, (0, 0), (settings.camera_width, settings.camera_height), (25, 20, 20), -1)
        cv2.putText(frame, message, (60, settings.camera_height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 255), 2)
        cv2.putText(frame, "FaceAttend System Standby - Configure in Settings", (60, settings.camera_height // 2 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
        return frame

