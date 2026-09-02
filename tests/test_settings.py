import os
import json
import tempfile
import pytest
from config.settings import AppSettings

def test_settings_save_and_load():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        custom_settings = AppSettings(
            camera_index=1,
            similarity_metric="l2",
            recognition_threshold=0.55,
            confirmation_frames=5,
            min_face_size=80,
            blur_threshold=40.0
        )
        custom_settings.save(path)
        assert os.path.exists(path)

        loaded = AppSettings.load(path)
        assert loaded.camera_index == 1
        assert loaded.similarity_metric == "l2"
        assert loaded.recognition_threshold == 0.55
        assert loaded.confirmation_frames == 5
        assert loaded.min_face_size == 80
        assert loaded.blur_threshold == 40.0
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_settings_load_nonexistent():
    loaded = AppSettings.load("/nonexistent/path/config.json")
    assert isinstance(loaded, AppSettings)
    assert loaded.camera_index == 0

def test_settings_camera_source_parsing():
    # Integer index as string
    s1 = AppSettings(camera_source="1")
    assert s1.get_capture_source() == 1

    # HTTP IP webcam stream URL
    s2 = AppSettings(camera_source="http://192.168.1.100:8080/video")
    assert s2.get_capture_source() == "http://192.168.1.100:8080/video"

    # RTSP stream URL
    s3 = AppSettings(camera_source="rtsp://192.168.1.50:554/live")
    assert s3.get_capture_source() == "rtsp://192.168.1.50:554/live"

def test_settings_foreign_os_path_resolution(tmp_path):
    # Simulate a config saved on a completely different Linux or Mac user's machine
    foreign_config = {
        "camera_index": 0,
        "detection_model_path": "/home/alien_user/ikshi/models/face_detection/face_detection_yunet_2023mar.onnx",
        "recognition_model_path": "/Users/alien_mac/ikshi/models/sface/face_recognition_sface_2021dec.onnx",
        "db_path": "C:\\Users\\alien_win\\ikshi\\data\\attendance.db"
    }
    cfg_file = tmp_path / "foreign_config.json"
    with open(cfg_file, "w") as f:
        json.dump(foreign_config, f)

    loaded = AppSettings.load(str(cfg_file))
    # Must resolve cleanly to this current repository's models and database paths
    assert os.path.isabs(loaded.detection_model_path)
    assert "face_detection_yunet_2023mar.onnx" in loaded.detection_model_path
    assert "face_recognition_sface_2021dec.onnx" in loaded.recognition_model_path
    assert "attendance.db" in loaded.db_path

def test_settings_ir_liveness_configuration():
    s = AppSettings(
        enable_ir_liveness=True,
        ir_camera_index=2,
        ir_camera_source="2",
        ir_liveness_threshold=0.65,
        ir_fov_scale_x=1.1,
        ir_fov_scale_y=1.1,
        ir_offset_x=5,
        ir_offset_y=-3
    )
    assert s.enable_ir_liveness is True
    assert s.get_ir_capture_source() == 2
    assert s.ir_liveness_threshold == 0.65
    assert s.ir_fov_scale_x == 1.1

    # String source e.g. RTSP or URL
    s2 = AppSettings(ir_camera_source="http://192.168.1.101:8080/video")
    assert s2.get_ir_capture_source() == "http://192.168.1.101:8080/video"



