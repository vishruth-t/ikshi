"""
ikshi - Camera Worker Thread
Captures video frames from primary RGB camera and optional secondary IR sensor
using CameraManager, with graceful auto-recovery and fallback.
"""

import os
import sys
import cv2
import time
import logging
import numpy as np
from typing import Union, Tuple, Optional
from PySide6.QtCore import QThread, Signal, Slot
from camera.camera_manager import CameraManager, test_capture_device, open_video_capture, find_first_working_camera
from config.settings import settings

logger = logging.getLogger(__name__)


class CameraWorker(QThread):
    # Signals
    frame_received = Signal(np.ndarray)
    frames_captured = Signal(np.ndarray, object)
    camera_error = Signal(str)
    ir_status_changed = Signal(bool, str)

    def __init__(self, camera_source: Union[int, str] = None):
        super().__init__()
        self.camera_source = self._parse_source(
            camera_source if camera_source is not None else settings.get_capture_source()
        )
        self.ir_source = settings.get_ir_capture_source()
        self.enable_ir = settings.enable_ir_liveness
        self._running = False
        self._manager = CameraManager()

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
            
            if "://" in src_str:
                proto, rest = src_str.split("://", 1)
                if "/" not in rest:
                    src_str = f"{proto}://{rest}/video"
                elif rest.endswith("/"):
                    src_str = f"{proto}://{rest}video"

        return src_str

    def run(self):
        self._running = True
        logger.info(f"CameraWorker thread started (RGB: {self.camera_source}, IR: {self.ir_source}, IR Enabled: {self.enable_ir})")
        target_delay_ms = int(1000 / max(1, settings.camera_fps))
        retry_count = 0

        while self._running:
            # 1. Open and verify captures via CameraManager
            if not self._manager.is_opened():
                logger.info(f"Attempting connection to RGB source: {self.camera_source} (IR: {self.ir_source})")
                ok = self._manager.open(
                    rgb_source=self.camera_source,
                    ir_source=self.ir_source,
                    enable_ir=self.enable_ir
                )

                if ok:
                    retry_count = 0
                    logger.info(f"Connected to camera source: {self.camera_source}")
                    if self._manager.is_ir_active():
                        self.ir_status_changed.emit(True, f"IR Camera Active ({self.ir_source})")
                    elif self.enable_ir:
                        self.ir_status_changed.emit(False, f"IR Camera Unavailable ({self._manager.ir_failure_reason})")
                    else:
                        self.ir_status_changed.emit(False, "IR Liveness Disabled")
                else:
                    retry_count += 1
                    # Auto-Scan fallback for RGB camera if index not found
                    if isinstance(self.camera_source, int):
                        ir_exclude = [self.ir_source] if isinstance(self.ir_source, int) else [2]
                        alt_idx = find_first_working_camera(exclude_indices=ir_exclude)
                        if alt_idx is not None and alt_idx != self.camera_source:
                            logger.info(f"Camera index {self.camera_source} inactive. Auto-switching to Camera {alt_idx}.")
                            self.camera_source = alt_idx
                            settings.camera_source = str(alt_idx)
                            settings.camera_index = alt_idx
                            self.camera_error.emit(f"Switched to working Camera {alt_idx}")
                            continue

                        main_msg = f"Camera {self.camera_source} Not Found"
                        sub_msg = f"Attempt {retry_count} • Check Camera Connection"
                    else:
                        main_msg = f"Connecting to {self.camera_source}"
                        sub_msg = f"Attempt {retry_count} • Ensure network stream is live"

                    self.camera_error.emit(f"Camera unavailable ({self.camera_source}). Attempt {retry_count}")
                    fallback = self._create_placeholder_frame(main_msg, sub_msg)
                    self.frame_received.emit(fallback)
                    self.frames_captured.emit(fallback, None)

                    for _ in range(30):
                        if not self._running:
                            break
                        self.msleep(100)
                    continue

            # 2. Read synchronous live frame pair
            ret, frame_rgb, frame_ir = self._manager.read()
            if ret and frame_rgb is not None and frame_rgb.size > 0:
                self.frame_received.emit(frame_rgb)
                self.frames_captured.emit(frame_rgb, frame_ir)
                self.msleep(target_delay_ms)
            else:
                logger.warning(f"Frame read failure from {self.camera_source}. Reconnecting...")
                self.camera_error.emit("Stream connection lost. Reconnecting...")
                fallback = self._create_placeholder_frame(
                    f"Reconnecting to {self.camera_source}...",
                    "Camera feed interrupted — Re-establishing link"
                )
                self.frame_received.emit(fallback)
                self.frames_captured.emit(fallback, None)
                self._manager.release()
                for _ in range(10):
                    if not self._running:
                        break
                    self.msleep(100)

        self._manager.release()
        logger.info("CameraWorker stopped.")

    def update_source(self, new_source: Union[int, str], new_ir_source: Optional[Union[int, str]] = None, enable_ir: Optional[bool] = None):
        parsed_rgb = self._parse_source(new_source)
        parsed_ir = settings.get_ir_capture_source() if new_ir_source is None else new_ir_source
        active_ir = settings.enable_ir_liveness if enable_ir is None else enable_ir

        if (parsed_rgb == self.camera_source and
            parsed_ir == self.ir_source and
            active_ir == self.enable_ir and
            self.isRunning()):
            return

        logger.info(f"Switching camera sources -> RGB: {parsed_rgb}, IR: {parsed_ir}, IR Enabled: {active_ir}")
        self.stop()
        self.camera_source = parsed_rgb
        self.ir_source = parsed_ir
        self.enable_ir = active_ir
        self.start()

    def stop(self):
        self._running = False
        self.wait(1500)

    def _create_placeholder_frame(self, main_msg: str, sub_msg: str = "Configure in Settings") -> np.ndarray:
        frame = np.zeros((settings.camera_height, settings.camera_width, 3), dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (settings.camera_width, settings.camera_height), (22, 17, 11), -1)
        
        cx, cy = settings.camera_width // 2, settings.camera_height // 2 - 40
        cv2.circle(frame, (cx, cy), 45, (247, 166, 203), 2)
        cv2.circle(frame, (cx, cy), 15, (247, 166, 203), -1)

        (w1, h1), _ = cv2.getTextSize(main_msg, cv2.FONT_HERSHEY_DUPLEX, 0.75, 1)
        cv2.putText(frame, main_msg, (cx - w1 // 2, cy + 80), cv2.FONT_HERSHEY_DUPLEX, 0.75, (248, 250, 252), 1, cv2.LINE_AA)
        
        (w2, h2), _ = cv2.getTextSize(sub_msg, cv2.FONT_HERSHEY_DUPLEX, 0.50, 1)
        cv2.putText(frame, sub_msg, (cx - w2 // 2, cy + 115), cv2.FONT_HERSHEY_DUPLEX, 0.50, (148, 163, 184), 1, cv2.LINE_AA)
        
        return frame
