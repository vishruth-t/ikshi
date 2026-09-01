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
        if isinstance(src, int):
            return src
        src_str = str(src).strip()
        if src_str.isdigit():
            return int(src_str)
        
        # Handle network URLs
        if "." in src_str or ":" in src_str:
            if not (src_str.startswith("http://") or src_str.startswith("https://") or src_str.startswith("rtsp://")):
                src_str = "http://" + src_str
            
            # If user typed only IP:PORT without path (e.g. http://192.168.1.50:8080)
            if "://" in src_str:
                proto, rest = src_str.split("://", 1)
                if "/" not in rest:
                    src_str = f"{proto}://{rest}/video"
                elif rest.endswith("/"):
                    src_str = f"{proto}://{rest}video"

        return src_str

    def run(self):
        self._running = True
        logger.info(f"CameraWorker thread started for source: {self.camera_source}")
        target_delay_ms = int(1000 / max(1, settings.camera_fps))
        retry_count = 0

        while self._running:
            # 1. Open VideoCapture if not currently open
            if self._cap is None or not self._cap.isOpened():
                if self._cap is not None:
                    self._cap.release()
                    self._cap = None

                logger.info(f"Attempting to connect to camera source: {self.camera_source}")
                self._cap = cv2.VideoCapture(self.camera_source)
                
                # For network streams, set minimal buffer size to avoid frame queuing & lag
                if isinstance(self.camera_source, str):
                    try:
                        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    except Exception:
                        pass

                if not self._cap.isOpened():
                    retry_count += 1
                    err_msg = f"Connecting to {self.camera_source}... (Attempt {retry_count})"
                    logger.warning(err_msg)
                    self.camera_error.emit(err_msg)
                    
                    fallback = self._create_placeholder_frame(
                        f"Connecting to: {self.camera_source}",
                        f"Attempt {retry_count} — Ensure phone server is active on Wi-Fi"
                    )
                    self.frame_received.emit(fallback)
                    self.msleep(1500)
                    continue
                else:
                    retry_count = 0
                    logger.info(f"Successfully connected to camera source: {self.camera_source}")

            # 2. Read live frame from capture device / stream
            ret, frame = self._cap.read()
            if ret and frame is not None and frame.size > 0:
                self.frame_received.emit(frame)
                self.msleep(target_delay_ms)
            else:
                logger.warning(f"Failed to read frame from {self.camera_source}. Reconnecting...")
                self.camera_error.emit("Stream connection lost. Reconnecting...")
                fallback = self._create_placeholder_frame(
                    f"Reconnecting to {self.camera_source}...",
                    "Stream feed interrupted — Re-establishing link"
                )
                self.frame_received.emit(fallback)
                if self._cap is not None:
                    self._cap.release()
                    self._cap = None
                self.msleep(1000)

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

    def _create_placeholder_frame(self, main_msg: str, sub_msg: str = "Configure in Settings (⚙️)") -> np.ndarray:
        frame = np.zeros((settings.camera_height, settings.camera_width, 3), dtype=np.uint8)
        # Deep dark slate background
        cv2.rectangle(frame, (0, 0), (settings.camera_width, settings.camera_height), (22, 17, 11), -1)
        
        # Center aperture graphic / icon
        cx, cy = settings.camera_width // 2, settings.camera_height // 2 - 40
        cv2.circle(frame, (cx, cy), 45, (56, 189, 248), 2)
        cv2.circle(frame, (cx, cy), 15, (56, 189, 248), -1)

        # Primary Title
        (w1, h1), _ = cv2.getTextSize(main_msg, cv2.FONT_HERSHEY_DUPLEX, 0.75, 1)
        cv2.putText(frame, main_msg, (cx - w1 // 2, cy + 80), cv2.FONT_HERSHEY_DUPLEX, 0.75, (248, 250, 252), 1, cv2.LINE_AA)
        
        # Subtitle Status
        (w2, h2), _ = cv2.getTextSize(sub_msg, cv2.FONT_HERSHEY_DUPLEX, 0.55, 1)
        cv2.putText(frame, sub_msg, (cx - w2 // 2, cy + 115), cv2.FONT_HERSHEY_DUPLEX, 0.55, (148, 163, 184), 1, cv2.LINE_AA)
        
        return frame


