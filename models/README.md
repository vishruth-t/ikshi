# FaceAttend - Model Setup Instructions

FaceAttend relies strictly on **OpenCV DNN** ONNX models for local face detection and recognition.

## Required Models

1. **YuNet Face Detector**
   - **Filename**: `face_detection_yunet_2023mar.onnx`
   - **Target Location**: `models/face_detection/face_detection_yunet_2023mar.onnx`
   - **Source**: OpenCV Model Zoo (`https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet`)
   - **License**: Apache 2.0

2. **SFace Face Recognizer**
   - **Filename**: `face_recognition_sface_2021dec.onnx`
   - **Target Location**: `models/sface/face_recognition_sface_2021dec.onnx`
   - **Source**: OpenCV Model Zoo (`https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface`)
   - **License**: Apache 2.0

## Automatic Setup

Run the helper script from the root directory:

```bash
python models/download_models.py
```

## Manual Setup

If working offline, manually download the ONNX files from the URLs specified in `download_models.py` and place them into their respective subdirectories:

```text
models/
├── face_detection/
│   └── face_detection_yunet_2023mar.onnx
└── sface/
    └── face_recognition_sface_2021dec.onnx
```
