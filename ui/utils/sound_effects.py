"""
ikshi - Audio Feedback & Sound Effects
Generates and plays soft confirmation chimes on verified attendance.
"""

import os
import wave
import struct
import math
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

CHIME_DIR = os.path.join(settings.BASE_DIR, "data", "sounds")
CHIME_PATH = os.path.join(CHIME_DIR, "verified_chime.wav")


def ensure_chime_sound_exists() -> str:
    """Generate high-fidelity 2-tone melodic confirmation chime if not already created."""
    if os.path.exists(CHIME_PATH) and os.path.getsize(CHIME_PATH) > 100:
        return CHIME_PATH

    os.makedirs(CHIME_DIR, exist_ok=True)
    sample_rate = 44100
    duration = 0.22 # seconds
    freq1 = 659.25 # E5
    freq2 = 1046.50 # C6

    num_samples = int(sample_rate * duration)
    samples = []

    for i in range(num_samples):
        t = float(i) / sample_rate
        if t < 0.08:
            env = math.exp(-t * 28.0)
            val = 0.45 * env * math.sin(2.0 * math.pi * freq1 * t)
        else:
            t2 = t - 0.08
            env = math.exp(-t2 * 20.0)
            val = 0.60 * env * math.sin(2.0 * math.pi * freq2 * t2)

        int_val = int(val * 32767.0)
        samples.append(struct.pack('<h', int_val))

    with wave.open(CHIME_PATH, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(samples))

    return CHIME_PATH


class SoundManager:
    _instance = None

    def __init__(self):
        self._sound_path = ensure_chime_sound_exists()
        self._sound_effect = None
        self._init_player()

    def _init_player(self):
        try:
            from PySide6.QtMultimedia import QSoundEffect
            from PySide6.QtCore import QUrl
            self._sound_effect = QSoundEffect()
            self._sound_effect.setSource(QUrl.fromLocalFile(self._sound_path))
            self._sound_effect.setVolume(0.7)
        except Exception as e:
            logger.debug(f"QSoundEffect init note: {e}")
            self._sound_effect = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance

    def play_verified_chime(self):
        """Play confirmation sound when attendance is recorded."""
        if not getattr(settings, "enable_sound_chime", True):
            return

        try:
            if self._sound_effect is not None:
                self._sound_effect.play()
            else:
                # Fallback: non-blocking system sound playback
                import subprocess
                if os.name == "posix":
                    subprocess.Popen(
                        ["paplay", self._sound_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
        except Exception as e:
            logger.debug(f"Audio chime playback note: {e}")

    def play_attendance_chime(self):
        self.play_verified_chime()

# Convenience singleton instance
sound_chime = SoundManager.get_instance()

