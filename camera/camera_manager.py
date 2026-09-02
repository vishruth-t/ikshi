"""
ikshi - Camera Management Module
Provides unified capture management for RGB primary stream and secondary IR sensor
with platform-optimized OS backends and graceful degradation.

NON-GOALS & LIMITATIONS:
- Secondary IR sensor capture assumes flat 2D IR intensity stream (e.g. V4L2 GREY 640x360).
- If the configured IR device index is unavailable, capture degrades gracefully to RGB-only.
"""

import sys
import cv2
import time
import logging
import numpy as np
from typing import Union, Tuple, Optional, Dict, Any, List
from config.settings import settings

logger = logging.getLogger(__name__)

# Suppress noisy OpenCV internal C++ warnings for invalid hardware nodes
try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except Exception:
    pass


def open_video_capture(src: Union[int, str]) -> cv2.VideoCapture:
    """Platform-optimized VideoCapture instantiation with native OS driver backends."""
    # Convert string integer (e.g. "0", "2") to actual int
    if isinstance(src, str) and src.strip().isdigit():
        src = int(src.strip())

    if isinstance(src, int) or (isinstance(src, str) and src.startswith("/dev/video")):
        if sys.platform.startswith("linux"):
            # Linux Video4Linux2 backend
            cap = cv2.VideoCapture(src, cv2.CAP_V4L2)
            if cap.isOpened():
                return cap
        elif sys.platform == "win32":
            # Windows DirectShow backend
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
            if cap.isOpened():
                return cap
        elif sys.platform == "darwin":
            # macOS native AVFoundation backend
            cap = cv2.VideoCapture(src, cv2.CAP_AVFOUNDATION)
            if cap.isOpened():
                return cap
        return cv2.VideoCapture(src)
    else:
        # Network URL (e.g. HTTP / RTSP stream)
        return cv2.VideoCapture(src)


def test_capture_device(src: Union[int, str]) -> Tuple[bool, Optional[cv2.VideoCapture]]:
    """Test if a device or stream opens and successfully yields real video frames."""
    try:
        cap = open_video_capture(src)
        if cap and cap.isOpened():
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


def find_first_working_camera(max_devices: int = 6, exclude_indices: Optional[List[int]] = None) -> Optional[int]:
    """Scan available local camera indices to find the first working video capture device."""
    excluded = set(exclude_indices or [])
    for idx in range(max_devices):
        if idx in excluded:
            continue
        ok, cap = test_capture_device(idx)
        if ok and cap is not None:
            cap.release()
            return idx
    return None


class CameraManager:
    """
    Manages dual-camera capture feeds:
      1. Primary RGB Camera (webcam / IP stream)
      2. Secondary IR Sensor (Windows Hello / V4L2 8-bit GREY sensor)
    """

    def __init__(self):
        self.rgb_cap: Optional[cv2.VideoCapture] = None
        self.ir_cap: Optional[cv2.VideoCapture] = None
        self.rgb_source: Optional[Union[int, str]] = None
        self.ir_source: Optional[Union[int, str]] = None
        self.ir_enabled: bool = False
        self.ir_available: bool = False
        self.ir_failure_reason: str = ""

    def open(
        self,
        rgb_source: Union[int, str],
        ir_source: Optional[Union[int, str]] = None,
        enable_ir: bool = False
    ) -> bool:
        """
        Open the primary RGB capture device and optionally the secondary IR device.
        Gracefully handles missing or non-functional IR device without failing RGB stream.
        """
        self.release()

        self.rgb_source = rgb_source
        self.ir_source = ir_source
        self.ir_enabled = enable_ir
        self.ir_available = False
        self.ir_failure_reason = ""

        # 1. Open RGB primary capture
        ok_rgb, cap_rgb = test_capture_device(rgb_source)
        if ok_rgb and cap_rgb is not None:
            self.rgb_cap = cap_rgb
            logger.info(f"Primary RGB camera opened successfully on {rgb_source}")
        else:
            logger.error(f"Failed to open primary RGB camera on {rgb_source}")
            return False

        # 2. Open IR secondary capture if enabled
        if self.ir_enabled and ir_source is not None:
            self._init_ir_device(ir_source)

        return True

    def _init_ir_device(self, ir_source: Union[int, str]):
        """Attempt to open and verify the secondary IR device with graceful fallback."""
        try:
            logger.info(f"Probing secondary IR camera source: {ir_source}")
            ok_ir, cap_ir = test_capture_device(ir_source)
            if ok_ir and cap_ir is not None:
                self.ir_cap = cap_ir
                self.ir_available = True
                self.ir_failure_reason = ""
                logger.info(f"Secondary IR camera opened successfully on {ir_source}")
            else:
                self.ir_available = False
                self.ir_failure_reason = f"Device '{ir_source}' not responding or no frame data"
                logger.warning(
                    f"Secondary IR camera unavailable on {ir_source} ({self.ir_failure_reason}). "
                    "Gracefully continuing in RGB-only mode."
                )
        except Exception as e:
            self.ir_available = False
            self.ir_failure_reason = str(e)
            logger.warning(
                f"Exception opening secondary IR camera on {ir_source}: {e}. "
                "Gracefully continuing in RGB-only mode."
            )

    def read(self) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Read synchronous frame pair from primary RGB and secondary IR camera.
        Returns:
            (success, rgb_frame, ir_frame)
            - success: True if primary RGB frame read succeeded.
            - rgb_frame: 3-channel BGR image or None.
            - ir_frame: IR frame or None if IR disabled / failed.
        """
        if self.rgb_cap is None or not self.rgb_cap.isOpened():
            return False, None, None

        ret_rgb, frame_rgb = self.rgb_cap.read()
        if not ret_rgb or frame_rgb is None or frame_rgb.size == 0:
            return False, None, None

        frame_ir: Optional[np.ndarray] = None
        if self.ir_enabled and self.ir_available and self.ir_cap is not None:
            try:
                ret_ir, f_ir = self.ir_cap.read()
                if ret_ir and f_ir is not None and f_ir.size > 0:
                    frame_ir = f_ir
                else:
                    logger.debug("IR frame read yielded empty frame; continuing RGB-only for this cycle.")
            except Exception as e:
                logger.debug(f"Exception reading IR frame: {e}")

        return True, frame_rgb, frame_ir

    def is_opened(self) -> bool:
        """Check if primary RGB camera is open and active."""
        return self.rgb_cap is not None and self.rgb_cap.isOpened()

    def is_ir_active(self) -> bool:
        """Check if IR camera is enabled, opened, and yielding frames."""
        return self.ir_enabled and self.ir_available and self.ir_cap is not None and self.ir_cap.isOpened()

    def release(self):
        """Release both RGB and IR capture resources."""
        if self.rgb_cap is not None:
            try:
                self.rgb_cap.release()
            except Exception:
                pass
            self.rgb_cap = None

        if self.ir_cap is not None:
            try:
                self.ir_cap.release()
            except Exception:
                pass
            self.ir_cap = None

        self.ir_available = False
