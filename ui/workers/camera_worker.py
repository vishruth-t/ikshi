import os
import sys
import cv2
import time
import numpy as np
import logging
from typing import Union, Tuple, Optional
from PySide6.QtCore import QThread, Signal, Slot
from config.settings import settings

logger = logging.getLogger(__name__)

# Suppress noisy OpenCV internal C++ warnings for invalid hardware nodes
try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except Exception:
    pass

def open_video_capture(src: Union[int, str]) -> cv2.VideoCapture:
    """Platform-optimized VideoCapture instantiation with native OS driver backends."""
    if isinstance(src, int):
        if sys.platform == "darwin":
            # macOS native AVFoundation backend
            cap = cv2.VideoCapture(src, cv2.CAP_AVFOUNDATION)
            if cap.isOpened():
                return cap
        elif sys.platform == "win32":
            # Windows DirectShow backend
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
            if cap.isOpened():
                return cap
        elif sys.platform.startswith("linux"):
            # Linux Video4Linux2 backend
            cap = cv2.VideoCapture(src, cv2.CAP_V4L2)
            if cap.isOpened():
                return cap
        return cv2.VideoCapture(src)
    else:
        return cv2.VideoCapture(src)

def test_capture_device(src: Union[int, str]) -> Tuple[bool, Optional[cv2.VideoCapture]]:
    """Test if a device or stream opens and successfully yields real video frames."""
    try:
        cap = open_video_capture(src)
        if cap and cap.isOpened():
            # For network stream, buffer size 1
            if isinstance(src, str):
                try:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                return True, cap
            cap.release()
    except Exception as e:
        logger.debug(f"Capture probe exception on {src}: {e}")
    return False, None

def find_first_working_camera(max_devices: int = 6) -> Optional[int]:
    """Scan available local camera indices to find the first working video capture device."""
    for idx in range(max_devices):
        ok, cap = test_capture_device(idx)
        if ok and cap is not None:
            cap.release()
            return idx
    return None

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
            # 1. Open and verify VideoCapture
            if self._cap is None or not self._cap.isOpened():
                if self._cap is not None:
                    self._cap.release()
                    self._cap = None

                logger.info(f"Attempting to connect to camera source: {self.camera_source}")
                ok, cap = test_capture_device(self.camera_source)
                
                if ok and cap is not None:
                    self._cap = cap
                    retry_count = 0
                    logger.info(f"Successfully connected to camera source: {self.camera_source}")
                else:
                    # Connection failed on specified source
                    retry_count += 1

                    # Auto-Scan: If user selected an index (like 0) that is not a real capture device, auto-scan other indices
                    if isinstance(self.camera_source, int):
                        alt_idx = find_first_working_camera()
                        if alt_idx is not None and alt_idx != self.camera_source:
                            logger.info(f"Camera index {self.camera_source} is not active. Auto-switching to working Camera {alt_idx}.")
                            self.camera_source = alt_idx
                            settings.camera_source = str(alt_idx)
                            settings.camera_index = alt_idx
                            self.camera_error.emit(f"Switched to working Camera {alt_idx}")
                            continue

                        main_msg = f"Camera {self.camera_source} Not Found"
                        if sys.platform == "darwin":
                            sub_msg = f"Attempt {retry_count} • Enable Camera in macOS System Settings"
                        else:
                            sub_msg = f"Attempt {retry_count} • Connect USB Camera or use Phone in toolbar"
                    elif isinstance(self.camera_source, str) and ("127.0.0.1" in self.camera_source or "localhost" in self.camera_source):
                        main_msg = "Connecting to Phone USB"
                        sub_msg = f"Attempt {retry_count} • Click 'Forward USB (8080)' or start IP Webcam"
                    else:
                        main_msg = f"Connecting to {self.camera_source}"
                        sub_msg = f"Attempt {retry_count} • Ensure IP Webcam / DroidCam is active on Wi-Fi"

                    self.camera_error.emit(f"Camera unavailable ({self.camera_source}). Attempt {retry_count}")
                    fallback = self._create_placeholder_frame(main_msg, sub_msg)
                    self.frame_received.emit(fallback)
                    
                    # Backoff sleep before next retry (3 seconds)
                    for _ in range(30):
                        if not self._running:
                            break
                        self.msleep(100)
                    continue

            # 2. Read live frame from capture device / stream
            ret, frame = self._cap.read()
            if ret and frame is not None and frame.size > 0:
                self.frame_received.emit(frame)
                self.msleep(target_delay_ms)
            else:
                logger.warning(f"Frame read failure from {self.camera_source}. Reconnecting...")
                self.camera_error.emit("Stream connection lost. Reconnecting...")
                fallback = self._create_placeholder_frame(
                    f"Reconnecting to {self.camera_source}...",
                    "Camera feed interrupted — Re-establishing link"
                )
                self.frame_received.emit(fallback)
                if self._cap is not None:
                    self._cap.release()
                    self._cap = None
                for _ in range(10):
                    if not self._running:
                        break
                    self.msleep(100)

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
        self.wait(1500)


    def _create_placeholder_frame(self, main_msg: str, sub_msg: str = "Configure in Settings (⚙️)") -> np.ndarray:
        frame = np.zeros((settings.camera_height, settings.camera_width, 3), dtype=np.uint8)
        # Deep dark slate background
        cv2.rectangle(frame, (0, 0), (settings.camera_width, settings.camera_height), (22, 17, 11), -1)
        
        # Center aperture graphic / icon with #cba6f7 (BGR: 247, 166, 203)
        cx, cy = settings.camera_width // 2, settings.camera_height // 2 - 40
        cv2.circle(frame, (cx, cy), 45, (247, 166, 203), 2)
        cv2.circle(frame, (cx, cy), 15, (247, 166, 203), -1)

        # Primary Title
        (w1, h1), _ = cv2.getTextSize(main_msg, cv2.FONT_HERSHEY_DUPLEX, 0.75, 1)
        cv2.putText(frame, main_msg, (cx - w1 // 2, cy + 80), cv2.FONT_HERSHEY_DUPLEX, 0.75, (248, 250, 252), 1, cv2.LINE_AA)
        
        # Subtitle Status
        (w2, h2), _ = cv2.getTextSize(sub_msg, cv2.FONT_HERSHEY_DUPLEX, 0.50, 1)
        cv2.putText(frame, sub_msg, (cx - w2 // 2, cy + 115), cv2.FONT_HERSHEY_DUPLEX, 0.50, (148, 163, 184), 1, cv2.LINE_AA)
        
        return frame




