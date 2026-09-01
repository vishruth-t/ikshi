from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QComboBox, QLineEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Signal
from config.settings import settings

class SettingsPage(QWidget):
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("SYSTEM CONFIGURATION & CALIBRATION SETTINGS")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(title)

        # Mobile Webcam Instructions Banner
        help_card = QFrame()
        help_card.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border-left: 4px solid #38BDF8;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel {
                color: #CBD5E1;
                font-size: 12px;
            }
        """)
        help_layout = QVBoxLayout(help_card)
        help_title = QLabel("📱 How to Use Your Mobile Phone as a Webcam:")
        help_title.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 14px; margin-bottom: 4px;")
        help_text = QLabel(
            "1. Install free app 'IP Webcam' or 'DroidCam' on your Android or iPhone.\n"
            "2. Connect your phone and PC to the same Wi-Fi network.\n"
            "3. Start the server in the app (note the IP address shown, e.g. 192.168.1.50).\n"
            "4. Enter the video stream URL below (e.g. http://192.168.1.50:8080/video) and click 'Save & Apply Settings'."
        )
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        layout.addWidget(help_card)

        form = QFormLayout()
        form.setSpacing(12)

        # Camera Source with Presets
        cam_source_container = QWidget()
        cam_source_layout = QVBoxLayout(cam_source_container)
        cam_source_layout.setContentsMargins(0, 0, 0, 0)
        cam_source_layout.setSpacing(6)

        self.input_camera_source = QLineEdit(str(settings.camera_source or settings.camera_index))
        self.input_camera_source.setPlaceholderText("Device index (0, 1) or Stream URL (http://192.168.1.x:8080/video)")
        self.input_camera_source.setStyleSheet("background-color: #1E293B; color: white; border: 1px solid #334155; padding: 6px; border-radius: 4px;")

        preset_row = QHBoxLayout()
        btn_preset_usb = QPushButton("Default USB (0)")
        btn_preset_usb.setStyleSheet("background-color: #334155; color: #94A3B8; font-size: 11px; padding: 4px 8px; border-radius: 4px;")
        btn_preset_usb.clicked.connect(lambda: self.input_camera_source.setText("0"))

        btn_preset_ip = QPushButton("IP Webcam (8080)")
        btn_preset_ip.setStyleSheet("background-color: #334155; color: #94A3B8; font-size: 11px; padding: 4px 8px; border-radius: 4px;")
        btn_preset_ip.clicked.connect(lambda: self.input_camera_source.setText("http://192.168.1.100:8080/video"))

        btn_preset_droid = QPushButton("DroidCam (4747)")
        btn_preset_droid.setStyleSheet("background-color: #334155; color: #94A3B8; font-size: 11px; padding: 4px 8px; border-radius: 4px;")
        btn_preset_droid.clicked.connect(lambda: self.input_camera_source.setText("http://192.168.1.100:4747/video"))

        preset_row.addWidget(btn_preset_usb)
        preset_row.addWidget(btn_preset_ip)
        preset_row.addWidget(btn_preset_droid)
        preset_row.addStretch()

        cam_source_layout.addWidget(self.input_camera_source)
        cam_source_layout.addLayout(preset_row)

        self.input_metric = QComboBox()
        self.input_metric.addItems(["cosine", "l2"])
        self.input_metric.setCurrentText(settings.similarity_metric)

        self.input_threshold = QDoubleSpinBox()
        self.input_threshold.setRange(0.1, 1.0)
        self.input_threshold.setSingleStep(0.05)
        self.input_threshold.setValue(settings.recognition_threshold)

        self.input_frames = QSpinBox()
        self.input_frames.setRange(1, 10)
        self.input_frames.setValue(settings.confirmation_frames)

        self.input_det_model = QLineEdit(settings.detection_model_path)
        self.input_rec_model = QLineEdit(settings.recognition_model_path)
        self.input_db_path = QLineEdit(settings.db_path)

        for widget in [self.input_metric, self.input_threshold, self.input_frames, self.input_det_model, self.input_rec_model, self.input_db_path]:
            widget.setStyleSheet("background-color: #1E293B; color: white; border: 1px solid #334155; padding: 6px; border-radius: 4px;")

        form.addRow("Camera Source (Device Index or URL):", cam_source_container)
        form.addRow("Similarity Metric:", self.input_metric)
        form.addRow("Recognition Similarity Threshold (0.1 - 1.0):", self.input_threshold)
        form.addRow("Temporal Confirmation Frames (N):", self.input_frames)
        form.addRow("YuNet Detection Model Path:", self.input_det_model)
        form.addRow("SFace Recognition Model Path:", self.input_rec_model)
        form.addRow("SQLite Database Path:", self.input_db_path)

        layout.addLayout(form)

        btn_save = QPushButton("💾 Save & Apply Settings")
        btn_save.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)

        layout.addStretch()

    def save_settings(self):
        cam_src = self.input_camera_source.text().strip()
        if not cam_src:
            cam_src = "0"

        settings.camera_source = cam_src
        if cam_src.isdigit():
            settings.camera_index = int(cam_src)
        
        settings.similarity_metric = self.input_metric.currentText()
        settings.recognition_threshold = self.input_threshold.value()
        settings.confirmation_frames = self.input_frames.value()
        settings.detection_model_path = self.input_det_model.text().strip()
        settings.recognition_model_path = self.input_rec_model.text().strip()
        settings.db_path = self.input_db_path.text().strip()

        settings.save()
        self.settings_saved.emit()
        QMessageBox.information(self, "Settings Saved", f"Application settings successfully saved!\nActive camera source: {cam_src}")


