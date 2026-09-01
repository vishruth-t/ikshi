from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QComboBox, QLineEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Signal, Qt
from config.settings import settings

class SettingsPage(QWidget):
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header Row
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("SYSTEM CONFIGURATION & CALIBRATION")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;")
        subtitle = QLabel("Configure camera sources, neural network thresholds, and storage paths")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        # Mobile Webcam Instructions Banner
        help_card = QFrame()
        help_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(56, 189, 248, 0.12), stop:1 rgba(37, 99, 235, 0.08));
                border-left: 4px solid #38BDF8;
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-left-width: 4px;
                border-radius: 12px;
                padding: 12px 16px;
            }
            QLabel {
                color: #CBD5E1;
                font-size: 12px;
            }
        """)
        help_layout = QVBoxLayout(help_card)
        help_layout.setContentsMargins(8, 4, 8, 4)
        help_layout.setSpacing(4)

        help_title = QLabel("📱 Quick Mobile Webcam Instructions:")
        help_title.setStyleSheet("color: #38BDF8; font-weight: 800; font-size: 13px; background: transparent; border: none;")
        help_text = QLabel(
            "1. Install free app 'IP Webcam' or 'DroidCam' on your Android or iPhone.\n"
            "2. Connect your phone & PC to the same Wi-Fi network and start server in the app.\n"
            "3. Enter the stream URL below (e.g. http://192.168.1.50:8080/video) and click 'Save Settings'."
        )
        help_text.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent; border: none;")
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        layout.addWidget(help_card)

        # Settings Form Card
        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #111827);
                border: 1px solid #334155;
                border-radius: 14px;
                padding: 16px;
            }
        """)
        form_card_layout = QVBoxLayout(form_card)
        form_card_layout.setContentsMargins(16, 16, 16, 16)
        form_card_layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)

        input_style = """
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #090D16;
                color: #F8FAFC;
                border: 1px solid #334155;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #3B82F6;
            }
        """

        # Camera Source with Presets
        cam_source_container = QWidget()
        cam_source_layout = QVBoxLayout(cam_source_container)
        cam_source_layout.setContentsMargins(0, 0, 0, 0)
        cam_source_layout.setSpacing(6)

        self.input_camera_source = QLineEdit(str(settings.camera_source or settings.camera_index))
        self.input_camera_source.setPlaceholderText("Device index (0, 1) or Stream URL (http://192.168.1.x:8080/video)")
        self.input_camera_source.setStyleSheet(input_style)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)

        def make_preset_btn(text, val):
            b = QPushButton(text)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #94A3B8;
                    border: 1px solid #334155;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 10px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: white;
                }
            """)
            b.clicked.connect(lambda: self.input_camera_source.setText(val))
            return b

        preset_row.addWidget(make_preset_btn("USB Camera (0)", "0"))
        preset_row.addWidget(make_preset_btn("IP Webcam (8080)", "http://192.168.1.100:8080/video"))
        preset_row.addWidget(make_preset_btn("DroidCam (4747)", "http://192.168.1.100:4747/video"))
        preset_row.addStretch()

        cam_source_layout.addWidget(self.input_camera_source)
        cam_source_layout.addLayout(preset_row)

        self.input_metric = QComboBox()
        self.input_metric.addItems(["cosine", "l2"])
        self.input_metric.setCurrentText(settings.similarity_metric)
        self.input_metric.setStyleSheet(input_style)

        self.input_threshold = QDoubleSpinBox()
        self.input_threshold.setRange(0.1, 1.0)
        self.input_threshold.setSingleStep(0.05)
        self.input_threshold.setValue(settings.recognition_threshold)
        self.input_threshold.setStyleSheet(input_style)

        self.input_frames = QSpinBox()
        self.input_frames.setRange(1, 10)
        self.input_frames.setValue(settings.confirmation_frames)
        self.input_frames.setStyleSheet(input_style)

        self.input_det_model = QLineEdit(settings.detection_model_path)
        self.input_det_model.setStyleSheet(input_style)

        self.input_rec_model = QLineEdit(settings.recognition_model_path)
        self.input_rec_model.setStyleSheet(input_style)

        self.input_db_path = QLineEdit(settings.db_path)
        self.input_db_path.setStyleSheet(input_style)

        def make_lbl(t):
            l = QLabel(t)
            l.setStyleSheet("color: #CBD5E1; font-weight: 600; font-size: 12px; border: none; background: transparent;")
            return l

        form.addRow(make_lbl("Camera Source (Index or URL):"), cam_source_container)
        form.addRow(make_lbl("Similarity Metric:"), self.input_metric)
        form.addRow(make_lbl("Cosine Similarity Threshold:"), self.input_threshold)
        form.addRow(make_lbl("Temporal Confirmation Frames (N):"), self.input_frames)
        form.addRow(make_lbl("YuNet Detection Model Path:"), self.input_det_model)
        form.addRow(make_lbl("SFace Recognition Model Path:"), self.input_rec_model)
        form.addRow(make_lbl("SQLite Database Path:"), self.input_db_path)

        form_card_layout.addLayout(form)
        layout.addWidget(form_card)

        btn_save = QPushButton("💾 Save & Apply System Settings")
        btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                color: white;
                font-weight: 800;
                font-size: 13px;
                padding: 12px 24px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
            }
        """)
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save, alignment=Qt.AlignRight)

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



