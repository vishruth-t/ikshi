import os
import shutil
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QComboBox, QLineEdit, QPushButton, QMessageBox, QFrame, QFileDialog, QCheckBox,
    QGridLayout, QSlider, QDialog, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Signal, Qt
from config.settings import settings
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS

class SettingsPage(QWidget):
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Header Row
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_label = QLabel("System Settings")
        self.subtitle_label = QLabel("Configure academic defaults, camera feeds, recognition parameters, and data backups")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        layout.addLayout(title_box)

        self.section_cards = []
        self.section_titles = []
        self.form_labels = []

        def make_section_frame(title_text: str) -> tuple[QFrame, QFormLayout]:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #161B22;
                    border: 1px solid #30363D;
                    border-radius: 6px;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(14, 12, 14, 12)
            c_layout.setSpacing(10)

            sec_title = QLabel(title_text)
            sec_title.setStyleSheet("color: #F0F6FC; font-weight: 700; font-size: 13px; border: none; background: transparent;")
            c_layout.addWidget(sec_title)

            self.section_cards.append(card)
            self.section_titles.append(sec_title)

            form = QFormLayout()
            form.setSpacing(12)
            c_layout.addLayout(form)
            return card, form

        def make_lbl(t: str) -> QLabel:
            l = QLabel(t)
            l.setStyleSheet("color: #8B949E; font-weight: 600; font-size: 12px; border: none; background: transparent;")
            self.form_labels.append(l)
            return l

        # 1. GENERAL SETTINGS
        gen_card, gen_form = make_section_frame("1. General Configuration")
        self.input_app_name = QLineEdit(settings.app_name)

        self.input_theme = QComboBox()
        self.input_theme.addItem("🌙 Dark Mode (Default)", "dark")
        self.input_theme.addItem("☀️ Light Mode", "light")
        for idx in range(self.input_theme.count()):
            if self.input_theme.itemData(idx) == getattr(settings, "theme", "dark"):
                self.input_theme.setCurrentIndex(idx)
                break

        self.input_default_dept = QComboBox()
        self.input_default_dept.addItems(DEFAULT_DEPARTMENTS)
        if settings.default_department in DEFAULT_DEPARTMENTS:
            self.input_default_dept.setCurrentText(settings.default_department)

        self.input_default_year = QComboBox()
        self.input_default_year.addItems(DEFAULT_ACADEMIC_YEARS)
        if settings.default_academic_year in DEFAULT_ACADEMIC_YEARS:
            self.input_default_year.setCurrentText(settings.default_academic_year)

        gen_form.addRow(make_lbl("Application Name:"), self.input_app_name)
        gen_form.addRow(make_lbl("Interface Theme:"), self.input_theme)
        gen_form.addRow(make_lbl("Default Department:"), self.input_default_dept)
        gen_form.addRow(make_lbl("Default Academic Year:"), self.input_default_year)
        layout.addWidget(gen_card)

        # 2. CAMERA SETTINGS
        cam_card, cam_form = make_section_frame("2. Camera Source")
        cam_container = QWidget()
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(0, 0, 0, 0)
        cam_layout.setSpacing(6)

        cam_row = QHBoxLayout()
        self.input_camera_source = QLineEdit(str(settings.camera_source or settings.camera_index))
        self.input_camera_source.setPlaceholderText("Device index (0, 1) or Stream URL")
        cam_row.addWidget(self.input_camera_source, stretch=1)

        btn_test_conn = QPushButton("Test Feed")
        btn_test_conn.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7;
                color: #11111B;
                font-size: 12px;
                font-weight: 700;
                padding: 7px 12px;
                border-radius: 6px;
                border: 1px solid #cba6f7;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        btn_test_conn.clicked.connect(self.test_camera_connection)
        cam_row.addWidget(btn_test_conn)
        cam_layout.addLayout(cam_row)

        # Quick preset buttons
        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)
        def make_preset_btn(text, val):
            b = QPushButton(text)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #21262D;
                    color: #C9D1D9;
                    border: 1px solid #30363D;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #30363D;
                    color: white;
                }
            """)
            b.clicked.connect(lambda: self.input_camera_source.setText(val))
            return b

        preset_row.addWidget(make_preset_btn("Built-in / USB Camera (0)", "0"))
        preset_row.addWidget(make_preset_btn("Wi-Fi IP Webcam", "http://192.168.1.100:8080/video"))
        preset_row.addWidget(make_preset_btn("USB Forwarded Port (8080)", "http://127.0.0.1:8080/video"))
        preset_row.addStretch()

        btn_adb_forward = QPushButton("Forward Phone USB (8080)")
        btn_adb_forward.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #cba6f7;
                border: 1px solid #30363D;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #30363D;
            }
        """)
        btn_adb_forward.clicked.connect(lambda: self.forward_adb_port(8080))
        preset_row.addWidget(btn_adb_forward)

        cam_layout.addLayout(preset_row)

        cam_form.addRow(make_lbl("Camera Feed:"), cam_container)
        layout.addWidget(cam_card)

        # 3. IR CAMERA ANTI-SPOOFING & LIVENESS
        ir_card, ir_form = make_section_frame("3. IR Camera Anti-Spoofing & Liveness")
        
        self.chk_enable_ir = QCheckBox("Enable IR-camera-based anti-spoofing liveness check")
        self.chk_enable_ir.setChecked(settings.enable_ir_liveness)
        self.chk_enable_ir.setStyleSheet("""
            QCheckBox {
                color: #F0F6FC;
                font-size: 12px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #30363D;
                border-radius: 4px;
                background-color: #0D1117;
            }
            QCheckBox::indicator:checked {
                background-color: #cba6f7;
                border: 1px solid #cba6f7;
            }
        """)

        ir_cam_row = QHBoxLayout()
        self.input_ir_source = QLineEdit(str(settings.ir_camera_source or settings.ir_camera_index))
        self.input_ir_source.setPlaceholderText("IR Device index (default: 2)")
        ir_cam_row.addWidget(self.input_ir_source, stretch=1)

        btn_test_ir = QPushButton("Test IR Sensor")
        btn_test_ir.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #cba6f7;
                border: 1px solid #30363D;
                font-size: 11px;
                font-weight: 600;
                padding: 7px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #30363D;
            }
        """)
        btn_test_ir.clicked.connect(self.test_ir_connection)
        ir_cam_row.addWidget(btn_test_ir)

        btn_calibrate_ir = QPushButton("Calibrate Alignment")
        btn_calibrate_ir.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #58A6FF;
                border: 1px solid #30363D;
                font-size: 11px;
                font-weight: 600;
                padding: 7px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #30363D;
            }
        """)
        btn_calibrate_ir.clicked.connect(self.open_ir_calibration_dialog)
        ir_cam_row.addWidget(btn_calibrate_ir)

        self.input_ir_threshold = QDoubleSpinBox()
        self.input_ir_threshold.setRange(0.10, 0.90)
        self.input_ir_threshold.setSingleStep(0.05)
        self.input_ir_threshold.setValue(settings.ir_liveness_threshold)

        ir_help = QLabel("Heuristic anti-spoofing layer analyzing 2D IR intensity, texture variance, and screen glare/blackout patterns.")
        ir_help.setStyleSheet("color: #8B949E; font-size: 11px;")
        ir_help.setWordWrap(True)

        ir_form.addRow(make_lbl("Anti-Spoofing:"), self.chk_enable_ir)
        ir_form.addRow(make_lbl("IR Camera Device:"), ir_cam_row)
        ir_form.addRow(make_lbl("Liveness Pass Threshold:"), self.input_ir_threshold)
        ir_form.addRow(make_lbl("Note:"), ir_help)
        layout.addWidget(ir_card)

        # 4. ATTENDANCE & RECOGNITION
        rec_card, rec_form = make_section_frame("4. Attendance & Recognition")
        
        self.input_threshold = QDoubleSpinBox()
        self.input_threshold.setRange(0.20, 0.80)
        self.input_threshold.setSingleStep(0.02)
        self.input_threshold.setValue(settings.recognition_threshold)

        self.input_frames = QSpinBox()
        self.input_frames.setRange(1, 10)
        self.input_frames.setValue(settings.confirmation_frames)

        self.chk_enable_audio = QCheckBox("Play pleasant confirmation chime on verified attendance")
        self.chk_enable_audio.setChecked(getattr(settings, "enable_sound_chime", True))
        self.chk_enable_audio.setStyleSheet("""
            QCheckBox {
                color: #F0F6FC;
                font-size: 12px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #30363D;
                border-radius: 4px;
                background-color: #0D1117;
            }
            QCheckBox::indicator:checked {
                background-color: #cba6f7;
                border: 1px solid #cba6f7;
            }
        """)

        rec_form.addRow(make_lbl("Match Sensitivity (Cosine):"), self.input_threshold)
        rec_form.addRow(make_lbl("Consecutive Confirmation Frames:"), self.input_frames)
        rec_form.addRow(make_lbl("Audio Feedback:"), self.chk_enable_audio)
        layout.addWidget(rec_card)

        # 5. DATA & SYSTEM
        data_card, data_form = make_section_frame("5. Data & Backups")
        
        db_row = QHBoxLayout()
        self.input_db_path = QLineEdit(settings.db_path)
        db_row.addWidget(self.input_db_path, stretch=1)

        btn_backup = QPushButton("Backup Database")
        btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #F0F6FC;
                border: 1px solid #30363D;
                padding: 7px 12px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #30363D;
            }
        """)
        btn_backup.clicked.connect(self.backup_database)
        db_row.addWidget(btn_backup)

        data_form.addRow(make_lbl("Database File:"), db_row)
        layout.addWidget(data_card)

        # Save Button
        btn_save = QPushButton("Save System Settings")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 9px 20px;
                border-radius: 6px;
                border: 1px solid #2EA043;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
        """)
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save, alignment=Qt.AlignRight)

        layout.addStretch()

    def backup_database(self):
        src_path = self.input_db_path.text().strip()
        if not os.path.exists(src_path):
            QMessageBox.warning(self, "Backup Warning", f"Database file not found at:\n{src_path}")
            return

        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database Backup",
            "attendance_backup.db",
            "SQLite Database (*.db *.sqlite);;All Files (*.*)"
        )
        if dest_path:
            try:
                shutil.copy2(src_path, dest_path)
                QMessageBox.information(self, "Backup Successful", f"Database successfully backed up to:\n{dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Backup Failed", f"Failed to backup database:\n{e}")

    def save_settings(self):
        cam_src = self.input_camera_source.text().strip() or "0"
        settings.camera_source = cam_src
        if cam_src.isdigit():
            settings.camera_index = int(cam_src)
        
        settings.app_name = self.input_app_name.text().strip() or "IKSHI"
        settings.theme = self.input_theme.currentData() or "dark"
        settings.default_department = self.input_default_dept.currentText()

        settings.default_academic_year = self.input_default_year.currentText()
        settings.recognition_threshold = self.input_threshold.value()
        settings.confirmation_frames = self.input_frames.value()
        settings.enable_sound_chime = self.chk_enable_audio.isChecked()
        settings.db_path = self.input_db_path.text().strip()

        # IR Anti-Spoofing & Liveness Settings
        settings.enable_ir_liveness = self.chk_enable_ir.isChecked()
        ir_src = self.input_ir_source.text().strip() or "2"
        settings.ir_camera_source = ir_src
        if ir_src.isdigit():
            settings.ir_camera_index = int(ir_src)
        settings.ir_liveness_threshold = self.input_ir_threshold.value()

        settings.save()
        self.settings_saved.emit()
        status_ir = "Enabled" if settings.enable_ir_liveness else "Disabled"
        QMessageBox.information(
            self,
            "Settings Saved",
            f"Application settings saved successfully!\n"
            f"RGB Camera Source: {cam_src}\n"
            f"IR Liveness Check: {status_ir} (Device {ir_src}, Threshold {settings.ir_liveness_threshold:.2f})\n"
            f"Audio Feedback: {'Enabled' if settings.enable_sound_chime else 'Disabled'}"
        )

    def apply_theme(self, theme_name: str = None):
        from ui.utils.theme import get_palette
        theme = theme_name or getattr(settings, "theme", "dark")
        p = get_palette(theme)

        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {p['text_primary']}; letter-spacing: -0.2px; background: transparent; border: none;")
        self.subtitle_label.setStyleSheet(f"font-size: 12px; color: {p['text_secondary']}; background: transparent; border: none;")

        for card in getattr(self, "section_cards", []):
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {p['bg_card']};
                    border: 1px solid {p['border']};
                    border-radius: 6px;
                }}
            """)
        for sec_t in getattr(self, "section_titles", []):
            sec_t.setStyleSheet(f"color: {p['card_header_color']}; font-weight: 700; font-size: 13px; border: none; background: transparent;")
        for lbl in getattr(self, "form_labels", []):
            lbl.setStyleSheet(f"color: {p['text_secondary']}; font-weight: 600; font-size: 12px; border: none; background: transparent;")

    def open_ir_calibration_dialog(self):
        """Open interactive visual alignment overlay calibration dialog for IR sensor."""
        from PySide6.QtWidgets import QDialog, QSlider, QFormLayout, QRadioButton, QButtonGroup
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QImage, QPixmap
        from vision.image_utils import cv_to_qimage
        from camera.camera_manager import test_capture_device, open_video_capture

        dialog = QDialog(self)
        dialog.setWindowTitle("IR-RGB Sensor Parallax Alignment Tool")
        dialog.setFixedWidth(740)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 10px;
            }
            QLabel {
                color: #F0F6FC;
            }
        """)

        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(12)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("🎯 IR-RGB Sensor Parallax Alignment")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F0F6FC;")
        sub = QLabel("Adjust Scale and Offset until the IR frame lines up with the RGB camera video. Align facial features with the crosshairs.")
        sub.setStyleSheet("font-size: 12px; color: #8B949E;")
        sub.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(sub)
        d_layout.addLayout(title_box)

        # View Mode Toggle Row
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        lbl_vmode = QLabel("PREVIEW MODE:")
        lbl_vmode.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        mode_row.addWidget(lbl_vmode)

        self.calib_view_mode = "blend" # "blend", "side_by_side", "rgb", "ir"
        btn_mode_blend = QPushButton("🎭 50/50 Overlay Blend")
        btn_mode_sbs = QPushButton("🔲 Side-by-Side (RGB | IR)")
        btn_mode_rgb = QPushButton("📷 RGB Only")
        btn_mode_ir = QPushButton("🌑 IR Only")

        for b in (btn_mode_blend, btn_mode_sbs, btn_mode_rgb, btn_mode_ir):
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("background-color: #0D1117; color: #8B949E; border: 1px solid #30363D; padding: 4px 10px; border-radius: 4px; font-size: 11px;")

        btn_mode_blend.setStyleSheet("background-color: #cba6f7; color: #11111B; font-weight: 700; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px;")

        def set_mode(m: str, active_btn: QPushButton):
            self.calib_view_mode = m
            for b in (btn_mode_blend, btn_mode_sbs, btn_mode_rgb, btn_mode_ir):
                b.setStyleSheet("background-color: #0D1117; color: #8B949E; border: 1px solid #30363D; padding: 4px 10px; border-radius: 4px; font-size: 11px;")
            active_btn.setStyleSheet("background-color: #cba6f7; color: #11111B; font-weight: 700; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px;")

        btn_mode_blend.clicked.connect(lambda: set_mode("blend", btn_mode_blend))
        btn_mode_sbs.clicked.connect(lambda: set_mode("side_by_side", btn_mode_sbs))
        btn_mode_rgb.clicked.connect(lambda: set_mode("rgb", btn_mode_rgb))
        btn_mode_ir.clicked.connect(lambda: set_mode("ir", btn_mode_ir))

        mode_row.addWidget(btn_mode_blend)
        mode_row.addWidget(btn_mode_sbs)
        mode_row.addWidget(btn_mode_rgb)
        mode_row.addWidget(btn_mode_ir)
        mode_row.addStretch()
        d_layout.addLayout(mode_row)

        # Video Preview Box
        preview_lbl = QLabel()
        preview_lbl.setFixedSize(700, 390)
        preview_lbl.setAlignment(Qt.AlignCenter)
        preview_lbl.setStyleSheet("border: 1px solid #30363D; border-radius: 8px; background-color: #0D1117;")
        d_layout.addWidget(preview_lbl)

        # Sliders Form
        sliders_card = QFrame()
        sliders_card.setStyleSheet("background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px; padding: 8px;")
        s_grid = QGridLayout(sliders_card)
        s_grid.setSpacing(10)

        # Scale X Slider (0.50 to 1.50)
        slider_sx = QSlider(Qt.Horizontal)
        slider_sx.setRange(50, 150)
        slider_sx.setValue(int(getattr(settings, "ir_fov_scale_x", 1.0) * 100))
        lbl_sx_val = QLabel(f"{getattr(settings, 'ir_fov_scale_x', 1.0):.2f}x")
        slider_sx.valueChanged.connect(lambda v: lbl_sx_val.setText(f"{v / 100.0:.2f}x"))

        # Scale Y Slider (0.50 to 1.50)
        slider_sy = QSlider(Qt.Horizontal)
        slider_sy.setRange(50, 150)
        slider_sy.setValue(int(getattr(settings, "ir_fov_scale_y", 1.0) * 100))
        lbl_sy_val = QLabel(f"{getattr(settings, 'ir_fov_scale_y', 1.0):.2f}x")
        slider_sy.valueChanged.connect(lambda v: lbl_sy_val.setText(f"{v / 100.0:.2f}x"))

        # Offset X Slider (-150 to 150 px)
        slider_ox = QSlider(Qt.Horizontal)
        slider_ox.setRange(-150, 150)
        slider_ox.setValue(getattr(settings, "ir_offset_x", 0))
        lbl_ox_val = QLabel(f"{getattr(settings, 'ir_offset_x', 0)} px")
        slider_ox.valueChanged.connect(lambda v: lbl_ox_val.setText(f"{v} px"))

        # Offset Y Slider (-150 to 150 px)
        slider_oy = QSlider(Qt.Horizontal)
        slider_oy.setRange(-150, 150)
        slider_oy.setValue(getattr(settings, "ir_offset_y", 0))
        lbl_oy_val = QLabel(f"{getattr(settings, 'ir_offset_y', 0)} px")
        slider_oy.valueChanged.connect(lambda v: lbl_oy_val.setText(f"{v} px"))

        s_grid.addWidget(QLabel("<b>Horizontal Scale (X):</b>"), 0, 0)
        s_grid.addWidget(slider_sx, 0, 1)
        s_grid.addWidget(lbl_sx_val, 0, 2)

        s_grid.addWidget(QLabel("<b>Vertical Scale (Y):</b>"), 1, 0)
        s_grid.addWidget(slider_sy, 1, 1)
        s_grid.addWidget(lbl_sy_val, 1, 2)

        s_grid.addWidget(QLabel("<b>Horizontal Offset (X):</b>"), 2, 0)
        s_grid.addWidget(slider_ox, 2, 1)
        s_grid.addWidget(lbl_ox_val, 2, 2)

        s_grid.addWidget(QLabel("<b>Vertical Offset (Y):</b>"), 3, 0)
        s_grid.addWidget(slider_oy, 3, 1)
        s_grid.addWidget(lbl_oy_val, 3, 2)

        d_layout.addWidget(sliders_card)

        # Open video captures safely
        rgb_cap = open_video_capture(settings.get_capture_source())
        raw_ir = self.input_ir_source.text().strip() or "2"
        ir_src = int(raw_ir) if raw_ir.isdigit() else raw_ir
        ir_cap = open_video_capture(ir_src)

        timer = QTimer(dialog)

        # Initialize optional face detector for auto-align
        yunet_detector = None
        if os.path.exists(settings.detection_model_path):
            try:
                yunet_detector = cv2.FaceDetectorYN.create(
                    model=settings.detection_model_path,
                    config="",
                    input_size=(640, 360),
                    score_threshold=0.6,
                    nms_threshold=0.3
                )
            except Exception as e:
                logger.debug(f"YuNet init in calibration dialog: {e}")

        # Current frames cache for auto-alignment button
        current_frames = {"rgb": None, "ir": None}

        def update_frame():
            try:
                ret_rgb, f_rgb = rgb_cap.read() if rgb_cap and rgb_cap.isOpened() else (False, None)
                ret_ir, f_ir = ir_cap.read() if ir_cap and ir_cap.isOpened() else (False, None)

                if ret_rgb and f_rgb is not None:
                    current_frames["rgb"] = f_rgb.copy()
                else:
                    f_rgb = np.zeros((360, 640, 3), dtype=np.uint8)
                    cv2.putText(f_rgb, "RGB Camera Offline", (200, 180), cv2.FONT_HERSHEY_DUPLEX, 0.7, (200, 200, 200), 1)

                if ret_ir and f_ir is not None:
                    current_frames["ir"] = f_ir.copy()
                else:
                    f_ir = np.zeros((360, 640), dtype=np.uint8)
                    cv2.putText(f_ir, "IR Sensor Offline", (210, 220), cv2.FONT_HERSHEY_DUPLEX, 0.7, 200, 1)

                # Resize to 640x360 for uniform processing
                rgb_res = cv2.resize(f_rgb, (640, 360))
                if len(f_ir.shape) == 2:
                    ir_3ch = cv2.cvtColor(f_ir, cv2.COLOR_GRAY2BGR)
                elif f_ir.shape[2] == 1:
                    ir_3ch = cv2.cvtColor(f_ir, cv2.COLOR_GRAY2BGR)
                else:
                    ir_3ch = f_ir
                ir_res = cv2.resize(ir_3ch, (640, 360))

                # Apply live calibration transform to IR
                sx = slider_sx.value() / 100.0
                sy = slider_sy.value() / 100.0
                ox = slider_ox.value()
                oy = slider_oy.value()

                M = np.float32([
                    [sx, 0, ox + (640 * (1 - sx) / 2)],
                    [0, sy, oy + (360 * (1 - sy) / 2)]
                ])
                ir_warped = cv2.warpAffine(ir_res, M, (640, 360))

                # Render depending on view mode
                mode = getattr(self, "calib_view_mode", "blend")
                if mode == "rgb":
                    display_frame = rgb_res
                elif mode == "ir":
                    display_frame = ir_warped
                elif mode == "side_by_side":
                    # Side-by-side comparison: left RGB (320x360), right warped IR (320x360)
                    rgb_half = cv2.resize(rgb_res, (350, 390))
                    ir_half = cv2.resize(ir_warped, (350, 390))
                    cv2.putText(rgb_half, "RGB Primary", (10, 25), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 128), 1)
                    cv2.putText(ir_half, "Transformed IR", (10, 25), cv2.FONT_HERSHEY_DUPLEX, 0.6, (203, 166, 247), 1)
                    display_frame = np.hstack([rgb_half, ir_half])
                else:  # "blend"
                    display_frame = cv2.addWeighted(rgb_res, 0.55, ir_warped, 0.45, 0)
                    cx, cy = 320, 180
                    cv2.line(display_frame, (cx - 40, cy), (cx + 40, cy), (0, 255, 128), 1)
                    cv2.line(display_frame, (cx, cy - 40), (cx, cy + 40), (0, 255, 128), 1)
                    cv2.circle(display_frame, (cx, cy), 80, (0, 255, 128), 1)

                qimg = cv_to_qimage(display_frame)
                preview_lbl.setPixmap(QPixmap.fromImage(qimg).scaled(preview_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception as e:
                logger.error(f"Error updating calibration frame: {e}")

        timer.timeout.connect(update_frame)
        timer.start(33) # ~30 FPS

        # Action Buttons Row
        btn_box = QHBoxLayout()
        btn_reset = QPushButton("Reset Defaults")
        btn_reset.setStyleSheet("background-color: #21262D; color: #8B949E; border: 1px solid #30363D; padding: 6px 12px; border-radius: 6px; font-weight: 500;")
        def do_reset():
            slider_sx.setValue(100)
            slider_sy.setValue(100)
            slider_ox.setValue(0)
            slider_oy.setValue(0)
        btn_reset.clicked.connect(do_reset)

        # Auto-Calibrate button using face detection
        btn_auto_align = QPushButton("✨ Auto-Align Face")
        btn_auto_align.setToolTip("Automatically calculates alignment scale and offset using face detection in both cameras")
        btn_auto_align.setStyleSheet("background-color: #21262D; color: #58A6FF; border: 1px solid #30363D; padding: 6px 12px; border-radius: 6px; font-weight: 600;")
        def do_auto_align():
            f_rgb = current_frames.get("rgb")
            f_ir = current_frames.get("ir")
            if f_rgb is None or f_ir is None or yunet_detector is None:
                QMessageBox.warning(dialog, "Auto-Align Warning", "Both RGB and IR camera feeds must be actively delivering video to auto-align.")
                return

            try:
                rgb_640 = cv2.resize(f_rgb, (640, 360))
                yunet_detector.setInputSize((640, 360))
                _, faces_rgb = yunet_detector.detect(rgb_640)

                ir_640 = cv2.resize(f_ir, (640, 360))
                if len(ir_640.shape) == 2:
                    ir_640 = cv2.cvtColor(ir_640, cv2.COLOR_GRAY2BGR)
                elif ir_640.shape[2] == 1:
                    ir_640 = cv2.cvtColor(ir_640, cv2.COLOR_GRAY2BGR)
                _, faces_ir = yunet_detector.detect(ir_640)

                if faces_rgb is None or len(faces_rgb) == 0:
                    QMessageBox.warning(dialog, "Face Not Found", "No face detected in the RGB camera. Please face the camera and try again.")
                    return
                if faces_ir is None or len(faces_ir) == 0:
                    QMessageBox.warning(dialog, "Face Not Found", "No face detected in the IR camera. Please face the camera and try again.")
                    return

                # Primary face in RGB and IR
                fb_rgb = faces_rgb[0][:4].astype(int)
                fb_ir = faces_ir[0][:4].astype(int)

                cx_rgb = fb_rgb[0] + fb_rgb[2] / 2.0
                cy_rgb = fb_rgb[1] + fb_rgb[3] / 2.0
                cx_ir = fb_ir[0] + fb_ir[2] / 2.0
                cy_ir = fb_ir[1] + fb_ir[3] / 2.0

                calc_ox = int(cx_rgb - cx_ir)
                calc_oy = int(cy_rgb - cy_ir)
                scale_ratio = float(fb_rgb[2]) / max(1.0, float(fb_ir[2]))

                calc_sx = max(50, min(150, int(scale_ratio * 100)))
                calc_sy = max(50, min(150, int(scale_ratio * 100)))

                slider_ox.setValue(max(-150, min(150, calc_ox)))
                slider_oy.setValue(max(-150, min(150, calc_oy)))
                slider_sx.setValue(calc_sx)
                slider_sy.setValue(calc_sy)

                QMessageBox.information(
                    dialog,
                    "Auto-Alignment Complete",
                    f"✓ Alignment computed:\nScale: {scale_ratio:.2f}x\nOffset: ({calc_ox} px, {calc_oy} px)"
                )
            except Exception as e:
                logger.error(f"Auto-alignment error: {e}")
                QMessageBox.warning(dialog, "Auto-Align Error", f"Failed to compute auto-alignment: {e}")

        btn_auto_align.clicked.connect(do_auto_align)

        btn_save_calib = QPushButton("Save & Apply Alignment")
        btn_save_calib.setStyleSheet("background-color: #238636; color: white; font-weight: 700; padding: 6px 16px; border-radius: 6px; border: 1px solid #2EA043;")
        def do_save():
            settings.ir_fov_scale_x = slider_sx.value() / 100.0
            settings.ir_fov_scale_y = slider_sy.value() / 100.0
            settings.ir_offset_x = slider_ox.value()
            settings.ir_offset_y = slider_oy.value()
            settings.save()
            self.settings_saved.emit()
            timer.stop()
            if rgb_cap: rgb_cap.release()
            if ir_cap: ir_cap.release()
            dialog.accept()
            QMessageBox.information(self, "Calibration Saved", "IR sensor alignment parameters saved and applied successfully!")

        btn_save_calib.clicked.connect(do_save)

        btn_close = QPushButton("Cancel")
        btn_close.setStyleSheet("background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; padding: 6px 14px; border-radius: 6px;")
        def do_cancel():
            timer.stop()
            if rgb_cap: rgb_cap.release()
            if ir_cap: ir_cap.release()
            dialog.reject()
        btn_close.clicked.connect(do_cancel)

        btn_box.addWidget(btn_reset)
        btn_box.addWidget(btn_auto_align)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        btn_box.addWidget(btn_save_calib)
        d_layout.addLayout(btn_box)

        dialog.finished.connect(lambda: [timer.stop(), rgb_cap.release() if rgb_cap else None, ir_cap.release() if ir_cap else None])
        dialog.exec()

    def test_ir_connection(self):
        """Test secondary IR camera device connectivity and display stream resolution/format."""
        import cv2
        from camera.camera_manager import test_capture_device

        raw_src = self.input_ir_source.text().strip() or "2"
        src = int(raw_src) if raw_src.isdigit() else raw_src
        ok, cap = test_capture_device(src)
        if ok and cap is not None:
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                channels = frame.shape[2] if len(frame.shape) > 2 else 1
                QMessageBox.information(
                    self,
                    "IR Camera Verified",
                    f"✓ Secondary IR Sensor (Device {src}) successfully opened!\n\n"
                    f"Resolution: {frame.shape[1]}x{frame.shape[0]} px\n"
                    f"Channels: {channels}\n\n"
                    f"Hardware ready for anti-spoofing verification."
                )
                return
        QMessageBox.warning(
            self,
            "IR Camera Not Found",
            f"✕ Unable to open IR camera device at index '{src}'.\n\n"
            f"If on Linux/Fedora, verify with `v4l2-ctl --list-devices` (e.g. /dev/video2).\n"
            f"Note: If the IR sensor is not connected, IKSHI gracefully runs in RGB-only mode."
        )

    def forward_adb_port(self, port: int = 8080):
        """Forward localhost TCP port to connected Android device over USB cable via ADB."""
        import subprocess
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=4)
            lines = [line.strip() for line in res.stdout.strip().split("\n")[1:] if line.strip() and "\tdevice" in line]
            
            if not lines:
                QMessageBox.warning(
                    self,
                    "No Android USB Device Detected",
                    "No Android phone detected via ADB.\n\n"
                    "Please check:\n"
                    "1. Phone is connected via USB cable.\n"
                    "2. 'USB Debugging' is enabled in Developer Options on your phone.\n"
                    "3. Accept the 'Allow USB debugging' prompt on your phone screen."
                )
                return False
            
            subprocess.run(["adb", "forward", f"tcp:{port}", f"tcp:{port}"], check=True, timeout=4)
            stream_url = f"http://127.0.0.1:{port}/video"
            self.input_camera_source.setText(stream_url)
            
            QMessageBox.information(
                self,
                "USB Connection Ready",
                f"Successfully forwarded USB port {port}!\n\n"
                f"Camera source set to: {stream_url}\n\n"
                f"Ensure the camera app is running on your phone, then click 'Save System Settings'."
            )
            return True
        except Exception as e:
            QMessageBox.critical(self, "ADB Command Error", f"Failed to execute adb forward: {e}")
            return False

    def test_camera_connection(self):
        """Test whether the configured camera index or stream URL is working and reachable."""
        import cv2
        import socket

        raw_src = self.input_camera_source.text().strip() or "0"

        # 1. Local Device Index
        if raw_src.isdigit():
            idx = int(raw_src)
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    QMessageBox.information(
                        self,
                        "Camera Verified",
                        f"✓ Local USB Camera (Index {idx}) successfully opened!\nResolution: {frame.shape[1]}x{frame.shape[0]} px"
                    )
                    return
            QMessageBox.warning(self, "Camera Test Failed", f"✕ Unable to open local camera device index {idx}.")
            return

        # 2. Network Stream URL
        url = raw_src
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("rtsp://")):
            url = "http://" + url
        if "://" in url:
            proto, rest = url.split("://", 1)
            if "/" not in rest:
                url = f"{proto}://{rest}/video"
            elif rest.endswith("/"):
                url = f"{proto}://{rest}video"

        # Check socket connectivity first
        try:
            host_port = url.split("://", 1)[1].split("/", 1)[0]
            host, port_str = host_port.split(":") if ":" in host_port else (host_port, "80")
            port = int(port_str)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            res = sock.connect_ex((host, port))
            sock.close()

            if res != 0:
                QMessageBox.critical(
                    self,
                    "Stream Unreachable",
                    f"✕ Cannot connect to {host}:{port} over the network.\n\n"
                    f"Troubleshooting:\n"
                    f"1. Is your phone on the SAME Wi-Fi or connected via USB?\n"
                    f"2. Is the IP Webcam or DroidCam app running on your phone?\n"
                    f"3. Verify the IP on your phone screen (e.g. {host})."
                )
                return
        except Exception as e:
            QMessageBox.critical(self, "Network Check Error", f"Network diagnostic failed: {e}")
            return

        # Test video stream capture
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None and frame.size > 0:
                self.input_camera_source.setText(url)
                QMessageBox.information(
                    self,
                    "Stream Verified",
                    f"✓ Successfully received video frames from mobile stream!\n\n"
                    f"Stream URL: {url}\n"
                    f"Resolution: {frame.shape[1]}x{frame.shape[0]} px\n\n"
                    f"Click 'Save System Settings' to apply."
                )
                return

        QMessageBox.warning(
            self,
            "Stream Video Read Failed",
            f"Connected to {host}:{port}, but could not decode video stream.\n\n"
            f"Ensure the URL ends in '/video' (e.g. http://{host}:{port}/video)."
        )





