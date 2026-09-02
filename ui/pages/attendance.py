from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit, QFormLayout, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Slot, Signal
from ui.widgets.camera_view import CameraViewWidget
from ui.widgets.attendance_table import AttendanceTableWidget
from ui.widgets.status_card import StatusCardWidget
from attendance.session_manager import SessionManager
from database.repositories import AttendanceRepository, StudentRepository
from config.settings import settings

class AttendancePage(QWidget):
    camera_source_changed = Signal(str)
    session_started = Signal()
    session_ended = Signal()

    def __init__(
        self,
        camera_view_widget: CameraViewWidget,
        session_manager: SessionManager,
        attendance_repo: AttendanceRepository,
        student_repo: StudentRepository,
        parent=None
    ):
        super().__init__(parent)
        self.camera_view = camera_view_widget
        self.session_manager = session_manager
        self.attendance_repo = attendance_repo
        self.student_repo = student_repo

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(20, 16, 20, 16)
        main_vbox.setSpacing(14)

        # 1. Top Header & Metric Cards Row
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        self.header_title = QLabel("Live Attendance")
        self.subtitle = QLabel("Real-time biometric recognition feed and session metrics")

        title_box.addWidget(self.header_title)
        title_box.addWidget(self.subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        self.ir_badge = QLabel("IR Anti-Spoof: Off")
        self.ir_badge.setStyleSheet("""
            background-color: #21262D;
            color: #8B949E;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_layout.addWidget(self.ir_badge)

        self.session_badge = QLabel("Standby")
        self.session_badge.setStyleSheet("""
            background-color: #21262D;
            color: #8B949E;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_layout.addWidget(self.session_badge)
        main_vbox.addWidget(header_container)

        # 4 Status Cards Row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_active_session = StatusCardWidget("Active Session", "None", "No session running")
        self.card_present = StatusCardWidget("Present Today", "0", "Students verified")
        self.card_absent = StatusCardWidget("Unverified", "0", "Students pending")
        self.card_total = StatusCardWidget("Total Directory", "0", "Enrolled students")

        cards_layout.addWidget(self.card_active_session)
        cards_layout.addWidget(self.card_present)
        cards_layout.addWidget(self.card_absent)
        cards_layout.addWidget(self.card_total)
        main_vbox.addLayout(cards_layout)

        # 2. Main Split Area: Camera & Session Controls (Left) | Live Roll (Right)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(16)

        # Left Column: Camera View & Session Controls
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        cam_header = QHBoxLayout()
        cam_header.setSpacing(8)

        self.cam_title = QLabel("Recognition Feed")

        cam_header.addWidget(self.cam_title)
        cam_header.addStretch()

        # Quick Camera Selector
        lbl_cam_src = QLabel("Camera:")
        lbl_cam_src.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: 500;")
        cam_header.addWidget(lbl_cam_src)

        self.cam_source_combo = QComboBox()
        self.cam_source_combo.addItem("Camera 0 (Default)", "0")
        self.cam_source_combo.addItem("Camera 1 (Secondary)", "1")
        self.cam_source_combo.addItem("Camera 2", "2")
        self.cam_source_combo.addItem("Phone USB (8080)", "http://127.0.0.1:8080/video")
        self.cam_source_combo.addItem("Phone Wi-Fi (8080)", "http://192.168.1.100:8080/video")

        current_src = str(settings.camera_source or settings.camera_index)
        for idx in range(self.cam_source_combo.count()):
            if self.cam_source_combo.itemData(idx) == current_src:
                self.cam_source_combo.setCurrentIndex(idx)
                break

        self.cam_source_combo.setStyleSheet("""
            QComboBox {
                background-color: #161B22;
                color: #F0F6FC;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QComboBox:focus, QComboBox:on {
                border: 1px solid #cba6f7;
            }
            QComboBox QAbstractItemView {
                background-color: #161B22;
                color: #F0F6FC;
                selection-background-color: #cba6f7;
                selection-color: #11111B;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px;
                outline: 0;
            }
            QComboBox QAbstractItemView::item {
                min-height: 24px;
                padding: 4px 8px;
                color: #F0F6FC;
                background-color: transparent;
                border-radius: 3px;
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
        """)

        self.cam_source_combo.currentIndexChanged.connect(self._on_cam_source_changed)
        cam_header.addWidget(self.cam_source_combo)

        left_col.addLayout(cam_header)
        left_col.addWidget(self.camera_view, stretch=1)

        # Session Setup Card
        self.session_card = QFrame()
        self.session_card.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(self.session_card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        form = QHBoxLayout()
        form.setSpacing(10)

        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("Class / Room (e.g. CS-101)")
        
        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("Subject (e.g. Computer Vision)")

        form.addWidget(self.input_class, stretch=1)
        form.addWidget(self.input_subject, stretch=1)

        self.btn_start = QPushButton("Start Session")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 16px;
                border-radius: 6px;
                border: 1px solid #2EA043;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
        """)
        self.btn_start.clicked.connect(self.toggle_session)
        form.addWidget(self.btn_start)

        card_layout.addLayout(form)
        left_col.addWidget(self.session_card)

        split_layout.addLayout(left_col, stretch=6)

        # Right Column: Live Attendance Roll Table
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        table_header = QHBoxLayout()
        self.table_title = QLabel("Live Attendance Roll")
        self.table_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #F0F6FC;")
        table_header.addWidget(self.table_title)
        table_header.addStretch()

        self.record_count_badge = QLabel("0 Verified")
        self.record_count_badge.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: 600;")
        table_header.addWidget(self.record_count_badge)

        right_col.addLayout(table_header)

        self.attendance_table = AttendanceTableWidget()
        right_col.addWidget(self.attendance_table, stretch=1)

        split_layout.addLayout(right_col, stretch=5)

        main_vbox.addLayout(split_layout, stretch=1)

    def toggle_session(self):
        if not self.session_manager.is_session_active():
            cls = self.input_class.text().strip() or "CS-101"
            subj = self.input_subject.text().strip() or "General Session"
            self.session_manager.start_session(subj, cls)
            self.btn_start.setText("End Session")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background-color: #DA3633;
                    color: white;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 7px 16px;
                    border-radius: 6px;
                    border: 1px solid #F85149;
                }
                QPushButton:hover {
                    background-color: #E5534B;
                }
            """)
            self.input_class.setEnabled(False)
            self.input_subject.setEnabled(False)
            self.session_started.emit()
        else:
            self.session_manager.end_session()
            self.btn_start.setText("Start Session")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background-color: #238636;
                    color: white;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 7px 16px;
                    border-radius: 6px;
                    border: 1px solid #2EA043;
                }
                QPushButton:hover {
                    background-color: #2EA043;
                }
            """)
            self.input_class.setEnabled(True)
            self.input_subject.setEnabled(True)
            self.session_ended.emit()
        self.refresh()

    @Slot()
    def update_ir_status(self, active: bool, message: str = ""):
        self.is_ir_hardware_active = active
        if active:
            self.ir_badge.setText("● IR Anti-Spoof: Active")
            self.ir_badge.setStyleSheet("""
                background-color: #162B1D;
                color: #3FB950;
                border: 1px solid #238636;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
        elif settings.enable_ir_liveness:
            self.ir_badge.setText("○ IR Sensor: Not Found (RGB Mode)")
            self.ir_badge.setStyleSheet("""
                background-color: #282114;
                color: #D29922;
                border: 1px solid #9E6A03;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
        else:
            self.ir_badge.setText("○ Standard Webcam (RGB Mode)")
            self.ir_badge.setStyleSheet("""
                background-color: #21262D;
                color: #8B949E;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)

    def apply_theme(self, theme_name: str = None):
        from ui.utils.theme import get_palette
        theme = theme_name or getattr(settings, "theme", "dark")
        p = get_palette(theme)
        
        self.header_title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {p['text_primary']}; letter-spacing: -0.2px; background: transparent; border: none;")
        self.subtitle.setStyleSheet(f"font-size: 12px; color: {p['text_secondary']}; background: transparent; border: none;")
        self.cam_title.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {p['text_primary']}; background: transparent; border: none;")
        self.table_title.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {p['text_primary']}; background: transparent; border: none;")
        
        if hasattr(self, "card_active_session"):
            self.card_active_session.apply_theme(theme)
            self.card_present.apply_theme(theme)
            self.card_absent.apply_theme(theme)
            self.card_total.apply_theme(theme)
        if hasattr(self, "attendance_table"):
            self.attendance_table.apply_theme(theme)
        self.refresh()

    def handle_attendance_marked(self, result):
        self.refresh()

    def refresh(self):
        stats = self.session_manager.get_session_stats()
        total_students = len(self.student_repo.get_all(active_only=True))

        if getattr(self, "is_ir_hardware_active", False):
            self.ir_badge.setText("● IR Anti-Spoof: Active")
            self.ir_badge.setStyleSheet("""
                background-color: #162B1D;
                color: #3FB950;
                border: 1px solid #238636;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
        elif settings.enable_ir_liveness:
            self.ir_badge.setText("○ IR Sensor: Not Found (RGB Mode)")
            self.ir_badge.setStyleSheet("""
                background-color: #282114;
                color: #D29922;
                border: 1px solid #9E6A03;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
        else:
            self.ir_badge.setText("○ Standard Webcam (RGB Mode)")
            self.ir_badge.setStyleSheet("""
                background-color: #21262D;
                color: #8B949E;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)

        if stats["active"]:
            self.session_badge.setText(f"Active: {stats['class_name']}")
            self.session_badge.setStyleSheet("""
                background-color: #238636;
                color: #FFFFFF;
                border: 1px solid #2EA043;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
            self.card_active_session.set_value(stats["class_name"], stats["subject"])
            present = stats["present_count"]
            absent = max(0, total_students - present)
            self.card_present.set_value(str(present), f"{stats['attendance_percentage']:.1f}% verified")
            self.card_absent.set_value(str(absent), f"{absent} pending")
            
            self.table_title.setText("Live Attendance Roll")
            self.record_count_badge.setText(f"{present} Verified")

            # Load active session records into table
            records = self.attendance_repo.get_session_attendance(stats["session_id"])
            self.attendance_table.set_data(records)

            if self.btn_start.text() != "End Session":
                self.btn_start.setText("End Session")
                self.btn_start.setStyleSheet("""
                    QPushButton {
                        background-color: #DA3633;
                        color: white;
                        font-weight: 600;
                        font-size: 12px;
                        padding: 7px 16px;
                        border-radius: 6px;
                        border: 1px solid #F85149;
                    }
                    QPushButton:hover {
                        background-color: #E5534B;
                    }
                """)
                self.input_class.setEnabled(False)
                self.input_subject.setEnabled(False)
                if stats.get("class_name"):
                    self.input_class.setText(stats["class_name"])
                if stats.get("subject"):
                    self.input_subject.setText(stats["subject"])
        else:
            self.session_badge.setText("Standby")
            self.session_badge.setStyleSheet("""
                background-color: #21262D;
                color: #8B949E;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
            self.card_active_session.set_value("Standby", "No active session")
            
            # Show today's recent attendance records when standby
            recent = self.attendance_repo.get_recent_attendance(30)
            self.card_present.set_value(str(len(recent)), "Recent records logged")
            self.card_absent.set_value(str(total_students), f"{total_students} in directory")
            
            self.table_title.setText("Recent Activity")
            self.record_count_badge.setText(f"{len(recent)} Logged")
            self.attendance_table.set_data(recent)

            if self.btn_start.text() != "Start Session":
                self.btn_start.setText("Start Session")
                self.btn_start.setStyleSheet("""
                    QPushButton {
                        background-color: #238636;
                        color: white;
                        font-weight: 600;
                        font-size: 12px;
                        padding: 7px 16px;
                        border-radius: 6px;
                        border: 1px solid #2EA043;
                    }
                    QPushButton:hover {
                        background-color: #2EA043;
                    }
                """)
                self.input_class.setEnabled(True)
                self.input_subject.setEnabled(True)

        self.card_total.set_value(str(total_students), "Enrolled students")

    def _on_cam_source_changed(self, index: int):
        new_src = self.cam_source_combo.itemData(index)
        if new_src is not None:
            settings.camera_source = str(new_src)
            if str(new_src).isdigit():
                settings.camera_index = int(new_src)
            settings.save()
            self.camera_source_changed.emit(str(new_src))

    def sync_camera_source(self):
        current_src = str(settings.camera_source or settings.camera_index)
        for idx in range(self.cam_source_combo.count()):
            if self.cam_source_combo.itemData(idx) == current_src:
                self.cam_source_combo.blockSignals(True)
                self.cam_source_combo.setCurrentIndex(idx)
                self.cam_source_combo.blockSignals(False)
                break




