# ikshi — On-Device Face Recognition Desktop Attendance System

**ikshi** is a high-performance, privacy-focused desktop application for automated real-time face recognition attendance tracking. Built with **PySide6 (Qt6)**, **OpenCV YuNet**, **OpenCV SFace**, and **SQLite (WAL mode)**, ikshi operates entirely on-device with zero cloud dependencies.

> [!IMPORTANT]
> **Strict Technology Constraint**: ikshi operates 100% locally on CPU/GPU via OpenCV DNN. It does **not** rely on Hugging Face, PyTorch, Transformers, or external cloud APIs. All face detection (`cv2.FaceDetectorYN`) and 128-D feature vector extraction (`cv2.FaceRecognizerSF`) run strictly on the local machine.

---

## Key Features

- **100% Local & Private**: Raw photos are never stored. Only 128-dimensional biometric embeddings are stored locally in SQLite (`data/attendance.db`).
- **Asynchronous Qt Pipeline**: Non-blocking background worker threads (`CameraWorker` and `RecognitionWorker`) ensure an ultra-responsive 30+ FPS GUI.
- **Smart Camera Auto-Discovery & Quick Switching**: Automatically probes and selects working hardware cameras across indices (`0`–`5`) and allows instant camera/phone switching directly from the live feed header.
- **Dynamic 3-Step Enrollment Wizard**: Guided multi-angle face enrollment (5 samples) with real-time quality validation (blur check, face size, centering, single-face verification).
- **Multi-Face Temporal Confirmation**: Multi-target tracking algorithm requiring consecutive identical identity matches to eliminate false positives and bounding box flicker.
- **Academic Year & Department Management**: Standardized dropdown filters across registration, student directory, and reports.
- **Exportable Reports**: Filter attendance sessions and student logs by department, academic year, subject, class, or date, and export directly to CSV (UTF-8-BOM formatted).
- **Minimalist Dark Theme**: Sleek, distraction-free UI styled with `#cba6f7` accenting and high-contrast dark controls.

---

## System Architecture & Project Structure

```text
ikshi/
│
├── app.py                            # Application entry point & logger initialization
│
├── config/
│   ├── constants.py                  # Standard departments, academic years & colors
│   ├── settings.py                   # Centralized runtime configuration & path resolution
│   └── app_config.json               # Persisted user settings
│
├── vision/
│   ├── face_detector.py              # OpenCV YuNet (cv2.FaceDetectorYN) wrapper
│   ├── face_aligner.py               # SFace alignCrop utilities
│   └── image_utils.py                # Quality validation, blur checks & Qt conversions
│
├── recognition/
│   ├── sface_model.py                # OpenCV SFace (cv2.FaceRecognizerSF) wrapper
│   ├── matcher.py                    # Cosine similarity vector matcher
│   └── threshold.py                  # Similarity thresholds & match evaluations
│
├── enrollment/
│   └── enrollment_service.py         # Multi-sample registration & re-enrollment service
│
├── attendance/
│   ├── attendance_service.py         # Attendance marking logic & session constraints
│   ├── session_manager.py            # Active session tracker & stats aggregator
│   └── temporal_confirmation.py      # Multi-frame temporal confirmation tracker
│
├── database/
│   ├── connection.py                 # Thread-safe SQLite connection with WAL mode
│   ├── models.py                     # Dataclasses (Student, FaceEmbedding, Attendance)
│   └── repositories.py               # Student, Embedding, Session & Attendance repositories
│
├── reports/
│   └── exporter.py                   # CSV export formatter with UTF-8-BOM
│
├── ui/
│   ├── main_window.py                # Main shell, collapsible sidebar & thread manager
│   ├── pages/
│   │   ├── attendance.py             # Merged Live Attendance feed, session control & metrics
│   │   ├── students.py               # Student directory with search & filters
│   │   ├── reports.py                # Historical attendance logs & CSV export
│   │   ├── registration.py           # 3-step student enrollment wizard
│   │   └── settings.py               # Camera source, thresholds & database backup

│   ├── widgets/
│   │   ├── camera_view.py            # Video feed with OpenCV box overlays
│   │   ├── attendance_table.py       # Live attendance roll widget
│   │   ├── student_table.py          # Student directory table widget
│   │   └── status_card.py            # Metric summary cards
│   └── workers/
│       ├── camera_worker.py          # Video capture QThread with auto-scan & backends
│       └── recognition_worker.py     # Background face recognition & tracker QThread
│
├── models/
│   ├── face_detection/               # face_detection_yunet_2023mar.onnx
│   ├── sface/                        # face_recognition_sface_2021dec.onnx
│   ├── download_models.py            # Automatic ONNX model downloader
│   └── README.md                     # Model sources and licensing
│
├── tests/                            # Pytest test suite (37 unit & integration tests)
├── requirements.txt                  # Python dependencies
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (Python 3.10, 3.11, 3.12, 3.13, or 3.14)
- A webcam, USB camera, or mobile phone (via USB/Wi-Fi)

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

> [!NOTE]
> **macOS Permissions**: When running on macOS, ensure camera access is enabled for your Terminal or IDE under **System Settings → Privacy & Security → Camera**.

---

## Using a Mobile Phone as Camera (USB / Wi-Fi)

ikshi natively supports using your smartphone as a high-definition webcam without third-party drivers:

### Option A: USB via ADB (Zero-Lag & Recommended)
1. Enable **USB Debugging** in *Settings → Developer Options* on your Android phone.
2. Connect your phone to your PC via USB cable.
3. Open **IP Webcam** (or **DroidCam**) on your phone and start the server.
4. In ikshi **Live Attendance**, select **Phone USB (8080)** from the camera dropdown above the video feed (or click **⚡ Forward Phone USB (8080)** in Settings).
5. Alternatively, run in terminal:
   ```bash
   adb forward tcp:8080 tcp:8080
   ```

### Option B: Android 14+ Native USB Webcam
1. Connect your Android 14+ phone via USB cable.
2. In the USB notification on your phone, choose **Webcam**.
3. Select **Camera 1** (or **Camera 2**) from the camera dropdown in ikshi.

### Option C: Local Wi-Fi Stream
1. Connect phone and PC to the same Wi-Fi network.
2. Start server in IP Webcam on your phone.
3. In ikshi **⚙️ Settings**, enter `http://<PHONE_IP>:8080/video` and click **Save & Apply Settings**.

---

## Running Automated Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

All 37 unit and integration tests verify:
- OpenCV YuNet & SFace model initialization and embeddings
- Student CRUD, cascades, and SQLite WAL durability
- Temporal confirmation multi-face tracking
- Dynamic face capture prompts and blur validation
- Department/Year filtering and CSV export

---

## Privacy & Biometric Security Notice

1. **Feature Vectors Only**: Raw facial images and student photos are never saved to disk. Only 128-dimensional floating point vectors are stored.
2. **Local Isolation**: All recognition and database operations are executed strictly on the local machine with no telemetry or external network calls.
3. **Data Deletion**: Disabling or deleting a student record removes all associated biometric feature vectors.