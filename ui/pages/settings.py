import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QComboBox, QLineEdit, QPushButton, QMessageBox, QFrame, QFileDialog
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
        title = QLabel("System Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #F0F6FC; letter-spacing: -0.2px;")
        subtitle = QLabel("Configure academic defaults, camera feeds, recognition parameters, and data backups")
        subtitle.setStyleSheet("font-size: 12px; color: #8B949E;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        input_style = """
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #0D1117;
                color: #F0F6FC;
                border: 1px solid #30363D;
                padding: 7px 10px;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QComboBox:on {
                border: 1px solid #cba6f7;
            }
            QComboBox QAbstractItemView {
                background-color: #161B22;
                color: #F0F6FC;
                selection-background-color: #cba6f7;
                selection-color: #11111B;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 4px;
                outline: 0;
            }
            QComboBox QAbstractItemView::item {
                min-height: 26px;
                padding: 4px 8px;
                color: #F0F6FC;
                background-color: transparent;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #21262D;
                color: #F0F6FC;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #cba6f7;
                color: #11111B;
                font-weight: 600;
            }
        """


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

            form = QFormLayout()
            form.setSpacing(10)
            c_layout.addLayout(form)
            return card, form

        def make_lbl(t: str) -> QLabel:
            l = QLabel(t)
            l.setStyleSheet("color: #8B949E; font-weight: 500; font-size: 12px; border: none; background: transparent;")
            return l

        # 1. GENERAL SETTINGS
        gen_card, gen_form = make_section_frame("1. General Configuration")
        self.input_app_name = QLineEdit(settings.app_name)
        self.input_app_name.setStyleSheet(input_style)

        self.input_default_dept = QComboBox()
        self.input_default_dept.addItems(DEFAULT_DEPARTMENTS)
        if settings.default_department in DEFAULT_DEPARTMENTS:
            self.input_default_dept.setCurrentText(settings.default_department)
        self.input_default_dept.setStyleSheet(input_style)

        self.input_default_year = QComboBox()
        self.input_default_year.addItems(DEFAULT_ACADEMIC_YEARS)
        if settings.default_academic_year in DEFAULT_ACADEMIC_YEARS:
            self.input_default_year.setCurrentText(settings.default_academic_year)
        self.input_default_year.setStyleSheet(input_style)

        gen_form.addRow(make_lbl("Application Name:"), self.input_app_name)
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
        self.input_camera_source.setStyleSheet(input_style)
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

        # 3. ATTENDANCE & RECOGNITION
        rec_card, rec_form = make_section_frame("3. Attendance & Recognition")
        
        self.input_threshold = QDoubleSpinBox()
        self.input_threshold.setRange(0.20, 0.80)
        self.input_threshold.setSingleStep(0.02)
        self.input_threshold.setValue(settings.recognition_threshold)
        self.input_threshold.setStyleSheet(input_style)

        self.input_frames = QSpinBox()
        self.input_frames.setRange(1, 10)
        self.input_frames.setValue(settings.confirmation_frames)
        self.input_frames.setStyleSheet(input_style)

        rec_form.addRow(make_lbl("Match Sensitivity (Cosine):"), self.input_threshold)
        rec_form.addRow(make_lbl("Consecutive Confirmation Frames:"), self.input_frames)
        layout.addWidget(rec_card)

        # 4. DATA & SYSTEM
        data_card, data_form = make_section_frame("4. Data & Backups")
        
        db_row = QHBoxLayout()
        self.input_db_path = QLineEdit(settings.db_path)
        self.input_db_path.setStyleSheet(input_style)
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
        
        settings.app_name = self.input_app_name.text().strip() or "ikshi"
        settings.default_department = self.input_default_dept.currentText()

        settings.default_academic_year = self.input_default_year.currentText()
        settings.recognition_threshold = self.input_threshold.value()
        settings.confirmation_frames = self.input_frames.value()
        settings.db_path = self.input_db_path.text().strip()

        settings.save()
        self.settings_saved.emit()
        QMessageBox.information(self, "Settings Saved", f"Application settings saved successfully!\nActive camera source: {cam_src}")

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





