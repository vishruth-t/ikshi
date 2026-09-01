from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal
from config.settings import settings

class SettingsPage(QWidget):
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("SYSTEM CONFIGURATION & CALIBRATION SETTINGS")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(15)

        self.input_camera = QSpinBox()
        self.input_camera.setRange(0, 10)
        self.input_camera.setValue(settings.camera_index)

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

        for widget in [self.input_camera, self.input_metric, self.input_threshold, self.input_frames, self.input_det_model, self.input_rec_model, self.input_db_path]:
            widget.setStyleSheet("background-color: #1E293B; color: white; border: 1px solid #334155; padding: 6px; border-radius: 4px;")

        form.addRow("Camera Source Index:", self.input_camera)
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
        settings.camera_index = self.input_camera.value()
        settings.similarity_metric = self.input_metric.currentText()
        settings.recognition_threshold = self.input_threshold.value()
        settings.confirmation_frames = self.input_frames.value()
        settings.detection_model_path = self.input_det_model.text().strip()
        settings.recognition_model_path = self.input_rec_model.text().strip()
        settings.db_path = self.input_db_path.text().strip()

        settings.save()
        self.settings_saved.emit()
        QMessageBox.information(self, "Settings Saved", "Application settings successfully saved and applied!")

