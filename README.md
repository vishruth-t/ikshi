# ikshi — On-Device Face Recognition Desktop Attendance System

**ikshi** is a high-performance, privacy-focused desktop application for automated real-time face recognition attendance tracking. Built with **PySide6 (Qt6)**, **OpenCV YuNet**, **OpenCV SFace**, and **SQLite (WAL mode)**, ikshi operates entirely on-device with zero cloud dependencies.

> [!IMPORTANT]
> **Strict Technology Constraint**: ikshi operates 100% locally on CPU/GPU via OpenCV DNN. It does **not** rely on Hugging Face, PyTorch, Transformers, or external cloud APIs. All face detection (`cv2.FaceDetectorYN`) and 128-D feature vector extraction (`cv2.FaceRecognizerSF`) run strictly on the local machine.

---

## Key Features

- **100% Local & Private**: Raw photos are never stored. Only 128-dimensional biometric embeddings are stored locally in SQLite (`data/attendance.db`).
- **In-Memory Vectorized Embedding Cache**: Ultra-fast matrix dot product lookup ($<0.05\text{ ms}$) across thousands of enrolled students without per-frame database I/O.
- **IR-Camera Anti-Spoofing & Forensic Auditing**: 2D infrared sensor verification layer with omni-directional bezel detection, planar lighting slopes, and automatic forensic dual-snapshot capture of spoof attempts into `data/security_audits/`.
- **Audio Feedback**: Subtle melodic confirmation chime played on verified attendance.
- **Visual IR-RGB Parallax Alignment Calibration**: Interactive real-time alpha-blend overlay tool in Settings with live scale and offset adjustment sliders.
- **Multi-Format Reports Exporter**: Export attendance logs to CSV, Excel XML (`.xls`), or styled printable HTML/PDF summaries with analytics metrics.
- **Student Profile & Photo Avatar Gallery**: Displays enrolled student avatar thumbnails and rich biometric profiles in the Student Directory.
- **Asynchronous Qt Pipeline**: Non-blocking background worker threads (`CameraWorker` and `RecognitionWorker`) ensure an ultra-responsive 30+ FPS GUI.
- **Smart Camera Auto-Discovery & Dual-Sensor Support**: Unified capture management via `CameraManager` supporting primary RGB webcams and secondary Windows Hello / V4L2 IR sensors (`/dev/video2`) with graceful fallback to RGB-only mode if the IR sensor is unavailable.
- **Dynamic Multi-Modal Enrollment Wizard**: Guided 2-stage face enrollment (5 samples with normal RGB camera + 5 samples with IR sensor) with live infrared preview and real-time quality validation.
- **Multi-Face Temporal Confirmation**: Multi-target tracking algorithm requiring consecutive identical identity matches to eliminate false positives and bounding box flicker.
- **Minimalist Dark Theme**: Sleek, distraction-free UI styled with `#cba6f7` accenting and high-contrast dark controls.

---

## System Architecture & Project Structure

```text
ikshi/
│
├── app.py                            # Application entry point & logger initialization
│
├── camera/
│   └── camera_manager.py             # Dual-camera capture manager (RGB + secondary IR) with auto-fallback
│
├── config/
│   ├── constants.py                  # Standard departments, academic years & colors
│   ├── settings.py                   # Centralized runtime configuration & path resolution
│   └── app_config.json               # Persisted user settings
│
├── vision/
│   ├── face_detector.py              # OpenCV YuNet (cv2.FaceDetectorYN) wrapper
│   ├── face_aligner.py               # SFace alignCrop utilities
│   ├── image_utils.py                # Quality validation, blur checks & Qt conversions
│   └── liveness_ir.py                # Infrared (IR) anti-spoofing & liveness detection
│
├── recognition/
│   ├── sface_model.py                # OpenCV SFace (cv2.FaceRecognizerSF) wrapper
│   ├── matcher.py                    # Vectorized matrix matcher with in-memory caching
│   └── threshold.py                  # Similarity thresholds & match evaluations
│
├── enrollment/
│   └── enrollment_service.py         # Multi-sample registration & re-enrollment service (RGB + IR)
│
├── attendance/
│   ├── attendance_service.py         # Attendance marking logic, liveness gates & session constraints
│   ├── session_manager.py            # Active session tracker & stats aggregator
│   └── temporal_confirmation.py      # Multi-frame temporal confirmation tracker
│
├── database/
│   ├── connection.py                 # Thread-safe SQLite connection with WAL mode & auto-migrations
│   ├── models.py                     # Dataclasses (Student, FaceEmbedding, Attendance, SecurityAudit)
│   └── repositories.py               # Student, Embedding, Session, Attendance & SecurityAudit repositories
│
├── reports/
│   └── exporter.py                   # CSV, Excel (.xls) and HTML printable summary report exporters
│
├── ui/
│   ├── main_window.py                # Main shell, collapsible sidebar & thread manager
│   ├── utils/
│   │   ├── icons.py                  # Anti-aliased vector QIcon drawer
│   │   └── sound_effects.py          # Audio confirmation chime player
│   ├── pages/
│   │   ├── attendance.py             # Live Attendance feed, on-demand session control & metrics
│   │   ├── students.py               # Student directory with search, photo avatars & profile dialog
│   │   ├── reports.py                # Historical attendance logs & Security & Spoof Audits
│   │   ├── registration.py           # 3-step student enrollment wizard with 5-pose guided capture
│   │   └── settings.py               # Camera source, IR alignment calibration tool & database backup
│   ├── widgets/
│   │   ├── camera_view.py            # Video feed with OpenCV box overlays & standby placeholder
│   │   ├── attendance_table.py       # Live attendance roll widget & Security Audits table
│   │   ├── student_table.py          # Student directory table widget with photo avatars
│   │   └── status_card.py            # Metric summary cards
│   └── workers/
│       ├── camera_worker.py          # Dual video capture QThread with auto-scan & backends
│       └── recognition_worker.py     # Background face recognition, IR liveness & spoof forensics
│
├── models/
│   ├── face_detection/               # face_detection_yunet_2023mar.onnx
│   ├── sface/                        # face_recognition_sface_2021dec.onnx
│   ├── download_models.py            # Automatic ONNX model downloader
│   └── README.md                     # Model sources and licensing
│
├── tests/                            # Pytest test suite (65 unit & integration tests)
├── requirements.txt                  # Python dependencies
└── README.md
```

---

## Infrared (IR) Anti-Spoofing & Liveness

ikshi includes an on-device anti-spoofing subsystem designed to work with secondary infrared camera sensors (such as Windows Hello sensors on Linux `/dev/video2` exposing 8-bit `GREY` frames at 640x360).

### Heuristic Signals Combined
1. **IR Texture & Sharpness Analysis (Laplacian Variance)**: Human facial skin and anatomical features exhibit rich continuous gradients in IR, whereas flat printed photos show flattened variance.
2. **Reflectance & Dynamic Range Sanity Check**: Detects harsh specular screen glare and OLED/LCD blackout patterns characteristic of mobile devices and tablet screens.
3. **Temporal Micro-Movement Variance**: Tracks physiological micro-tremors and subtle shifts across consecutive frames, distinguishing live faces from static photo cutouts.

### Non-Goals & Physical Limitations (Important)
- **No Structured-Light Projector**: This subsystem processes flat 2D infrared intensity frames; it does **not** generate 3D point clouds or Time-of-Flight (ToF) depth maps.
- **Casual Attack Surface Defense**: Designed specifically to prevent casual presentation attacks (paper photos, smartphone screens). High-end physical spoofing (e.g. customized 3D latex masks or IR-matched media) falls outside the threat model of flat 2D intensity heuristics.
- **Graceful Hardware Fallback**: If the configured IR sensor index is unavailable, disconnected, or fails to open, ikshi logs a warning and seamlessly runs in standard RGB-only mode without crashing or blocking attendance.

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (Python 3.10, 3.11, 3.12, 3.13, or 3.14)
- A webcam, USB camera, or mobile phone (via USB/Wi-Fi)
- Optional: Windows Hello-compatible IR sensor (e.g. `/dev/video2`) for IR anti-spoofing

### 2. Create Virtual Environment

**Linux / macOS**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch ikshi

```bash
python app.py
```

*(Required OpenCV ONNX models will download automatically to `models/` on the first launch if not already present).*

---

## Running Automated Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

All 51 unit and integration tests verify:
- Dual-camera manager (`CameraManager`) and graceful degradation
- IR anti-spoofing liveness detector (`IRLivenessDetector`) and coordinate mapping
- OpenCV YuNet & SFace model initialization and embeddings
- Student CRUD, cascades, and SQLite WAL durability with schema migrations
- Temporal confirmation multi-face tracking
- Dynamic face capture prompts and blur validation
- Department/Year filtering and CSV export with audit logs

---

## Privacy & Biometric Security Notice

1. **Feature Vectors Only**: Raw facial images and student photos are never saved to disk. Only 128-dimensional floating point vectors are stored.
2. **Local Isolation**: All recognition and database operations are executed strictly on the local machine with no telemetry or external network calls.
3. **Data Deletion**: Disabling or deleting a student record removes all associated biometric feature vectors.
'''bash
import cv2

def scan_cameras(max_tested=5):
    print("--- Scanning Camera Devices on Windows ---")
    for idx in range(max_tested):
        # 1. Try Media Foundation (Best for Windows IR / Windows Hello)
        cap_msmf = cv2.VideoCapture(idx, cv2.CAP_MSMF)
        if cap_msmf.isOpened():
            ret, frame = cap_msmf.read()
            if ret and frame is not None:
                print(f"[FOUND] Index {idx} opens with cv2.CAP_MSMF (Shape: {frame.shape})")
            cap_msmf.release()
        
        # 2. Try DirectShow
        cap_dshow = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap_dshow.isOpened():
            ret, frame = cap_dshow.read()
            if ret and frame is not None:
                print(f"[FOUND] Index {idx} opens with cv2.CAP_DSHOW (Shape: {frame.shape})")
            cap_dshow.release()

if __name__ == "__main__":
    scan_cameras()
'''