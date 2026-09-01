# FaceAttend — Local OpenCV SFace Desktop Attendance System

**FaceAttend** is a production-ready, modular desktop application for real-time automated face-recognition attendance tracking. It uses a webcam, OpenCV YuNet face detection, **OpenCV SFace** (`cv2.FaceRecognizerSF`) face recognition, PySide6 for GUI, and SQLite for persistence.

> [!IMPORTANT]
> **Strict Technology Constraint**: FaceAttend operates 100% locally and does **NOT** use Hugging Face, PyTorch, Transformers, or external cloud APIs. All face detection and recognition operations run locally using OpenCV DNN (`cv2.FaceDetectorYN` and `cv2.FaceRecognizerSF`).

---

## Key Features

- **Local & Private**: Biometric vectors are extracted and processed strictly on device.
- **Asynchronous Architecture**: Non-blocking Qt background workers (`CameraWorker` and `RecognitionWorker`) keep PySide6 GUI responsive.
- **3-Step Registration Wizard**: Guided enrollment workflow with multi-angle sample capture (5 samples) and quality validation (blur check, face size, single face).
- **Temporal Confirmation**: Requires $N$ consecutive identical frame recognitions to prevent false positives and flickering.
- **Duplicate Prevention**: Application and database-level `UNIQUE(session_id, student_id)` constraints prevent double attendance.
- **Historical Reports & CSV Exporter**: Filter logs by subject or class and export report data to CSV.
- **Calibratable Settings**: Configurable camera source, cosine similarity threshold (default 0.70), and temporal confirmation frame count.

---

## Project Structure

```text
face_attendance/
│
├── app.py                     # Entry point & application bootstrapper
├── config/
│   ├── settings.py            # App settings (thresholds, model paths, camera index)
│   └── app_config.json        # Saved user settings
│
├── camera/
│   └── camera_manager.py      # Camera capture manager
│
├── vision/
│   ├── face_detector.py       # OpenCV YuNet FaceDetectorYN wrapper
│   ├── face_aligner.py        # SFace alignCrop utilities
│   └── image_utils.py         # Blur checks, quality validation & Qt image conversion
│
├── recognition/
│   ├── sface_model.py         # OpenCV SFace cv2.FaceRecognizerSF wrapper
│   ├── matcher.py             # Cosine similarity matcher against DB vectors
│   └── threshold.py           # Threshold evaluator
│
├── enrollment/
│   └── enrollment_service.py  # Quality validation & sample collector
│
├── attendance/
│   ├── attendance_service.py  # Attendance recording logic & validation
│   ├── session_manager.py     # Active session tracker & stats aggregator
│   └── temporal_confirmation.py# Multi-frame (N-frame) temporal filter
│
├── database/
│   ├── connection.py          # SQLite connection manager with WAL mode
│   ├── models.py              # Dataclass schemas (Student, FaceEmbedding, Attendance)
│   └── repositories.py        # Student, Embedding, Session & Attendance repos
│
├── reports/
│   └── exporter.py            # CSV Exporter
│
├── ui/
│   ├── main_window.py         # Main Window with sidebar navigation
│   ├── pages/                 # Dashboard, Attendance, Registration, Students, Reports, Settings
│   ├── widgets/               # CameraView, AttendanceTable, StudentTable, StatusCard
│   └── workers/               # CameraWorker & RecognitionWorker QThreads
│
├── models/
│   ├── face_detection/        # face_detection_yunet_2023mar.onnx
│   ├── sface/                 # face_recognition_sface_2021dec.onnx
│   ├── download_models.py     # ONNX model setup helper script
│   └── README.md              # Model sources & licenses
│
├── tests/                     # Automated test suite (database, services, recognition)
├── requirements.txt           # Dependency requirements
└── README.md
```

---

## Installation & Setup

### 1. Create Virtual Environment

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

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Model Setup

Download the official OpenCV ONNX model weights (`YuNet` and `SFace`):

```bash
python models/download_models.py
```

Expected ONNX files:
- `models/face_detection/face_detection_yunet_2023mar.onnx`
- `models/sface/face_recognition_sface_2021dec.onnx`

---

## Running the Application

Launch FaceAttend:

```bash
python app.py
```

---

## Running Automated Tests

Run the full pytest suite:

```bash
pytest
```

---

## Using Mobile Phone as Webcam (Wi-Fi / USB)

FaceAttend natively supports connecting your smartphone camera via local Wi-Fi or USB:

### Option A: Using IP Webcam (Android)
1. Install **IP Webcam** from Google Play Store on your phone.
2. Connect your phone and PC to the same Wi-Fi network.
3. In the app, scroll to the bottom and tap **Start server**.
4. Note the URL shown on your phone screen (e.g. `http://192.168.1.50:8080`).
5. Open FaceAttend, go to **Settings** (`⚙️ Settings`), enter `http://192.168.1.50:8080/video` in **Camera Source**, and click **Save & Apply Settings**.

### Option B: Using DroidCam (Android / iOS)
1. Install **DroidCam** on your phone.
2. Start DroidCam and note the WiFi IP and port (e.g., `192.168.1.50` and port `4747`).
3. In FaceAttend Settings, set **Camera Source** to `http://192.168.1.50:4747/video` and click **Save & Apply Settings**.

### Option C: Virtual Camera via USB
1. Install DroidCam, Iriun Webcam, or EpocCam on your phone and PC client.
2. Select the virtual camera device index (e.g. `0`, `1`, `2`) in Settings.


---

## Privacy & Biometric Data Notice

1. **Biometric Storage**: Raw student photographs are not stored. Only 128-dimensional floating point feature vectors generated by OpenCV SFace are saved in `data/attendance.db`.
2. **Access Control**: Database storage is local. Backup and access control should be secured according to institutional policy.
3. **Data Deletion**: Disabling or deleting a student profile removes their enrolled feature vectors.