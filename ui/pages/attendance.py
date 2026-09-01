from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFormLayout, QFrame
)
from PySide6.QtCore import Qt, Slot
from ui.widgets.camera_view import CameraViewWidget
from ui.widgets.attendance_table import AttendanceTableWidget
from ui.widgets.status_card import StatusCardWidget
from attendance.session_manager import SessionManager
from database.repositories import AttendanceRepository, StudentRepository

class AttendancePage(QWidget):
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # Left Column: Camera View Widget
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        cam_header = QHBoxLayout()
        cam_title = QLabel("📷 LIVE RECOGNITION FEED")
        cam_title.setStyleSheet("font-weight: 800; font-size: 14px; color: #F1F5F9; letter-spacing: 0.5px;")

        cam_badge = QLabel("● REAL-TIME SFACE")
        cam_badge.setStyleSheet("""
            color: #34D399;
            background-color: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.5px;
        """)

        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        cam_header.addWidget(cam_badge)
        left_col.addLayout(cam_header)

        left_col.addWidget(self.camera_view, stretch=1)
        layout.addLayout(left_col, stretch=6)

        # Right Column: Controls & Real-Time Stats
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # Session Setup Card
        self.session_card = QFrame()
        self.session_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #111827);
                border: 1px solid #334155;
                border-radius: 14px;
                padding: 16px;
            }
        """)
        card_layout = QVBoxLayout(self.session_card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        card_title = QLabel("⚡ SESSION CONTROL")
        card_title.setStyleSheet("font-size: 12px; font-weight: 800; color: #94A3B8; letter-spacing: 1px; border: none; background: transparent;")
        card_layout.addWidget(card_title)

        form = QFormLayout()
        form.setSpacing(10)

        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("e.g. CS-101")
        self.input_class.setStyleSheet("""
            QLineEdit {
                background-color: #090D16;
                color: #F8FAFC;
                border: 1px solid #334155;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
        
        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("e.g. Computer Vision")
        self.input_subject.setStyleSheet("""
            QLineEdit {
                background-color: #090D16;
                color: #F8FAFC;
                border: 1px solid #334155;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)

        lbl_class = QLabel("Class / Batch:")
        lbl_class.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 12px; border: none; background: transparent;")
        
        lbl_subject = QLabel("Subject:")
        lbl_subject.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 12px; border: none; background: transparent;")

        form.addRow(lbl_class, self.input_class)
        form.addRow(lbl_subject, self.input_subject)
        card_layout.addLayout(form)

        self.btn_start = QPushButton("▶ Start Attendance Session")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                color: white;
                font-weight: 700;
                font-size: 13px;
                padding: 10px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
            }
        """)
        self.btn_start.clicked.connect(self.toggle_session)
        card_layout.addWidget(self.btn_start)

        right_col.addWidget(self.session_card)

        # Live Stats Card
        self.stats_card = StatusCardWidget("Present Count", "0", "Session inactive", "#3B82F6", icon="👥")
        right_col.addWidget(self.stats_card)

        # Live Attendance Table Section
        table_header = QHBoxLayout()
        table_title = QLabel("Live Session Roll")
        table_title.setStyleSheet("font-weight: 700; font-size: 14px; color: #F1F5F9;")
        table_header.addWidget(table_title)
        table_header.addStretch()
        right_col.addLayout(table_header)

        self.attendance_table = AttendanceTableWidget()
        right_col.addWidget(self.attendance_table, stretch=1)

        layout.addLayout(right_col, stretch=4)

    def toggle_session(self):
        if not self.session_manager.is_session_active():
            cls = self.input_class.text().strip() or "CS-101"
            subj = self.input_subject.text().strip() or "General Lecture"
            self.session_manager.start_session(subj, cls)
            self.btn_start.setText("⏹ End Attendance Session")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
                    color: white;
                    font-weight: 700;
                    font-size: 13px;
                    padding: 10px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B91C1C, stop:1 #DC2626);
                }
            """)
            self.input_class.setEnabled(False)
            self.input_subject.setEnabled(False)
        else:
            self.session_manager.end_session()
            self.btn_start.setText("▶ Start Attendance Session")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                    color: white;
                    font-weight: 700;
                    font-size: 13px;
                    padding: 10px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
                }
            """)
            self.input_class.setEnabled(True)
            self.input_subject.setEnabled(True)
        self.refresh()

    @Slot()
    def handle_attendance_marked(self, result):
        self.refresh()

    def refresh(self):
        stats = self.session_manager.get_session_stats()
        total_students = len(self.student_repo.get_all(active_only=True))

        if stats["active"]:
            present = stats["present_count"]
            self.stats_card.set_value(str(present), f"{stats['attendance_percentage']:.1f}% of {total_students} verified")
            records = self.attendance_repo.get_session_attendance(stats["session_id"])
            self.attendance_table.set_data(records)
            if self.btn_start.text() != "⏹ End Attendance Session":
                self.btn_start.setText("⏹ End Attendance Session")
                self.btn_start.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
                        color: white;
                        font-weight: 700;
                        font-size: 13px;
                        padding: 10px;
                        border-radius: 8px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B91C1C, stop:1 #DC2626);
                    }
                """)
                self.input_class.setEnabled(False)
                self.input_subject.setEnabled(False)
                if stats.get("class_name"):
                    self.input_class.setText(stats["class_name"])
                if stats.get("subject"):
                    self.input_subject.setText(stats["subject"])
        else:
            self.stats_card.set_value("0", "Session inactive - Click Start")
            self.attendance_table.set_data([])
            if self.btn_start.text() != "▶ Start Attendance Session":
                self.btn_start.setText("▶ Start Attendance Session")
                self.btn_start.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                        color: white;
                        font-weight: 700;
                        font-size: 13px;
                        padding: 10px;
                        border-radius: 8px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
                    }
                """)
                self.input_class.setEnabled(True)
                self.input_subject.setEnabled(True)

