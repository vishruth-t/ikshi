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
