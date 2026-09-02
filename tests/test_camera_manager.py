import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from camera.camera_manager import CameraManager, test_capture_device as probe_device


def test_camera_manager_rgb_only_success():
    manager = CameraManager()
    
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap.read.return_value = (True, fake_frame)

    with patch("camera.camera_manager.open_video_capture", return_value=mock_cap):
        ok = manager.open(rgb_source=0, enable_ir=False)
        assert ok is True
        assert manager.is_opened() is True
        assert manager.is_ir_active() is False

        ret, rgb, ir = manager.read()
        assert ret is True
        assert rgb is not None
        assert ir is None

        manager.release()
        assert manager.is_opened() is False


def test_camera_manager_dual_success():
    manager = CameraManager()

    mock_rgb = MagicMock()
    mock_rgb.isOpened.return_value = True
    fake_rgb = np.zeros((720, 1280, 3), dtype=np.uint8)
    mock_rgb.read.return_value = (True, fake_rgb)

    mock_ir = MagicMock()
    mock_ir.isOpened.return_value = True
    fake_ir = np.zeros((360, 640, 3), dtype=np.uint8)
    mock_ir.read.return_value = (True, fake_ir)

    def mock_open_cap(src):
        if src == 0:
            return mock_rgb
        elif src == 2:
            return mock_ir
        return MagicMock(isOpened=lambda: False)

    with patch("camera.camera_manager.open_video_capture", side_effect=mock_open_cap):
        ok = manager.open(rgb_source=0, ir_source=2, enable_ir=True)
        assert ok is True
        assert manager.is_opened() is True
        assert manager.is_ir_active() is True

        ret, rgb, ir = manager.read()
        assert ret is True
        assert rgb is not None
        assert ir is not None

        manager.release()
        assert manager.is_opened() is False
        assert manager.is_ir_active() is False


def test_camera_manager_ir_failure_graceful_degradation():
    manager = CameraManager()

    mock_rgb = MagicMock()
    mock_rgb.isOpened.return_value = True
    fake_rgb = np.zeros((720, 1280, 3), dtype=np.uint8)
    mock_rgb.read.return_value = (True, fake_rgb)

    # IR fails to open
    def mock_open_cap(src):
        if src == 0:
            return mock_rgb
        return MagicMock(isOpened=lambda: False, read=lambda: (False, None))

    with patch("camera.camera_manager.open_video_capture", side_effect=mock_open_cap):
        ok = manager.open(rgb_source=0, ir_source=2, enable_ir=True)
        # Primary RGB still succeeds
        assert ok is True
        assert manager.is_opened() is True
        # IR is marked inactive
        assert manager.is_ir_active() is False
        assert manager.ir_available is False
        assert "not responding" in manager.ir_failure_reason

        ret, rgb, ir = manager.read()
        assert ret is True
        assert rgb is not None
        assert ir is None # Gracefully None
