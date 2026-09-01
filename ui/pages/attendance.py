from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFormLayout, QGroupBox, QFrame
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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Left Column: Camera View Widget
        left_col = QVBoxLayout()
        cam_title = QLabel("LIVE CAMERA ATTENDANCE STREAM")
        cam_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #94A3B8;")
        left_col.addWidget(cam_title)
        left_col.addWidget(self.camera_view)
        layout.addLayout(left_col, stretch=6)

        # Right Column: Controls & Real-Time Stats
        right_col = QVBoxLayout()
        right_col.setSpacing(15)

        # Session Setup Box
        self.session_box = QGroupBox("Session Control")
        self.session_box.setStyleSheet("""
            QGroupBox {
                color: #F8FAFC;
                font-weight: bold;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        box_layout = QVBoxLayout(self.session_box)

        form = QFormLayout()
        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("e.g. CS-101")
        self.input_class.setStyleSheet("background-color: #0F172A; color: white; border: 1px solid #334155; padding: 6px; border-radius: 4px;")
        
        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("e.g. Computer Vision")
        self.input_subject.setStyleSheet("background-color: #0F172A; color: white; border: 1px solid #334155; padding: 6px; border-radius: 4px;")

        form.addRow("Class / Room:", self.input_class)
        form.addRow("Subject Name:", self.input_subject)
        box_layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Session")
        self.btn_start.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.btn_start.clicked.connect(self.toggle_session)

        btn_layout.addWidget(self.btn_start)
        box_layout.addLayout(btn_layout)

        right_col.addWidget(self.session_box)

        # Live Stats Card
        self.stats_card = StatusCardWidget("Present Count", "0", "Session inactive", "#3B82F6")
        right_col.addWidget(self.stats_card)

        # Live Attendance Table
        table_title = QLabel("Session Live Attendance Log")
        table_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #94A3B8;")
        right_col.addWidget(table_title)

        self.attendance_table = AttendanceTableWidget()
        right_col.addWidget(self.attendance_table)

        layout.addLayout(right_col, stretch=4)

    def toggle_session(self):
        if not self.session_manager.is_session_active():
            cls = self.input_class.text().strip() or "Class-A"
            subj = self.input_subject.text().strip() or "General Attendance"
            self.session_manager.start_session(subj, cls)
            self.btn_start.setText("End Session")
            self.btn_start.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
            self.input_class.setEnabled(False)
            self.input_subject.setEnabled(False)
        else:
            self.session_manager.end_session()
            self.btn_start.setText("Start Session")
            self.btn_start.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
            self.input_class.setEnabled(True)
            self.input_subject.setEnabled(True)
        self.refresh()

    def refresh(self):
        stats = self.session_manager.get_session_stats()
        if stats["active"]:
            self.stats_card.set_value(
                f"{stats['present_count']} / {stats['total_students']}",
                f"{stats['attendance_percentage']:.1f}% Present in {stats['subject']}"
            )
            records = self.attendance_repo.get_session_attendance(stats["session_id"])
            self.attendance_table.set_data(records)
        else:
            self.stats_card.set_value("0", "Session inactive")
            self.attendance_table.set_data([])
