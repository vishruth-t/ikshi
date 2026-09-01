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

        help_title = QLabel("🔌 USB Phone Connection (Zero Wi-Fi Lag & No Iriun Needed):")
        help_title.setStyleSheet("color: #38BDF8; font-weight: 800; font-size: 13px; background: transparent; border: none;")
        help_text = QLabel(
            "• Method 1 (USB Cable + ADB): Connect phone via USB with USB Debugging enabled, open IP Webcam or DroidCam, and click '🔌 Forward USB Port' below.\n"
            "• Method 2 (Android 14+ Native UVC): Plug phone via USB, tap USB charging notification -> Choose 'Webcam' -> select camera index (e.g. 0, 1, 2).\n"
            "• Method 3 (Wi-Fi): Enter phone Wi-Fi URL (e.g. http://192.168.x.x:8080/video)."
        )
        help_text.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent; border: none;")
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        layout.addWidget(help_card)

        # Settings Form Card
        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E293B, stop:1 #111827);
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

        # Camera Source with Presets & USB Tool
        cam_source_container = QWidget()
        cam_source_layout = QVBoxLayout(cam_source_container)
        cam_source_layout.setContentsMargins(0, 0, 0, 0)
        cam_source_layout.setSpacing(8)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_camera_source = QLineEdit(str(settings.camera_source or settings.camera_index))
        self.input_camera_source.setPlaceholderText("Device index (0, 1) or Stream URL (http://192.168.1.x:8080/video)")
        self.input_camera_source.setStyleSheet(input_style)
        input_row.addWidget(self.input_camera_source, stretch=1)

        btn_test_conn = QPushButton("📡 Test Stream Connection")
        btn_test_conn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        btn_test_conn.clicked.connect(self.test_camera_connection)
        input_row.addWidget(btn_test_conn)

        cam_source_layout.addLayout(input_row)

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
                    padding: 5px 10px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: white;
                }
            """)
            b.clicked.connect(lambda: self.input_camera_source.setText(val))
            return b

        btn_usb_default = make_preset_btn("Built-in USB (0)", "0")
        btn_wifi_ipwebcam = make_preset_btn("Wi-Fi IP Webcam", "http://192.168.1.100:8080/video")
        btn_usb_ipwebcam = make_preset_btn("USB ADB (127.0.0.1:8080)", "http://127.0.0.1:8080/video")
        btn_usb_droidcam = make_preset_btn("USB ADB (127.0.0.1:4747)", "http://127.0.0.1:4747/video")

        preset_row.addWidget(btn_usb_default)
        preset_row.addWidget(btn_wifi_ipwebcam)
        preset_row.addWidget(btn_usb_ipwebcam)
        preset_row.addWidget(btn_usb_droidcam)
        preset_row.addStretch()

        # USB ADB Forwarding Action Row
        adb_action_row = QHBoxLayout()
        adb_action_row.setSpacing(8)

        btn_adb_forward_8080 = QPushButton("⚡ Auto-Forward USB (IP Webcam 8080)")
        btn_adb_forward_8080.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.15);
                color: #38BDF8;
                border: 1px solid rgba(56, 189, 248, 0.35);
                font-size: 11px;
                font-weight: 700;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: white;
            }
        """)
        btn_adb_forward_8080.clicked.connect(lambda: self.forward_adb_port(8080))

        btn_adb_forward_4747 = QPushButton("⚡ Auto-Forward USB (DroidCam 4747)")
        btn_adb_forward_4747.setStyleSheet("""
            QPushButton {
                background-color: rgba(139, 92, 246, 0.15);
                color: #A78BFA;
                border: 1px solid rgba(139, 92, 246, 0.35);
                font-size: 11px;
                font-weight: 700;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
                color: white;
            }
        """)
        btn_adb_forward_4747.clicked.connect(lambda: self.forward_adb_port(4747))

        adb_action_row.addWidget(btn_adb_forward_8080)
        adb_action_row.addWidget(btn_adb_forward_4747)
        adb_action_row.addStretch()

        cam_source_layout.addLayout(preset_row)
        cam_source_layout.addLayout(adb_action_row)



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
                "USB ADB Connected!",
                f"Successfully forwarded USB port {port}!\n\n"
                f"Camera source set to: {stream_url}\n\n"
                f"Make sure the video server is started on your phone, then click 'Save & Apply System Settings'."
            )
            return True
        except Exception as e:
            QMessageBox.critical(self, "ADB Command Error", f"Failed to execute adb forward: {e}")
            return False

    def test_camera_connection(self):
        """Test whether the configured camera index or stream URL is working and reachable."""
        import cv2
        import socket

        raw_src = self.input_camera_source.text().strip()
        if not raw_src:
            raw_src = "0"

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
                        "Camera Test Passed!",
                        f"✓ Local USB Camera device (Index {idx}) successfully opened!\nResolution: {frame.shape[1]}x{frame.shape[0]} px"
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

        # Check Wi-Fi socket connectivity first
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
                    "Wi-Fi Stream Unreachable",
                    f"✕ Cannot connect to {host}:{port} over the network.\n\n"
                    f"Troubleshooting Guide:\n"
                    f"1. Is your phone on the SAME Wi-Fi as your computer?\n"
                    f"2. Is IP Webcam or DroidCam server started on your phone?\n"
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
                    "Wi-Fi Stream Verified!",
                    f"✓ Successfully received video frames from mobile stream!\n\n"
                    f"Stream URL: {url}\n"
                    f"Resolution: {frame.shape[1]}x{frame.shape[0]} px\n\n"
                    f"Click 'Save & Apply System Settings' to apply."
                )
                return

        QMessageBox.warning(
            self,
            "Stream Video Read Failed",
            f"Connected to {host}:{port}, but could not decode video stream.\n\n"
            f"Ensure the URL ends in '/video' (e.g. http://{host}:{port}/video)."
        )




