from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from ui.widgets.status_card import StatusCardWidget
from ui.widgets.attendance_table import AttendanceTableWidget
from attendance.session_manager import SessionManager
from database.repositories import StudentRepository, AttendanceRepository

class DashboardPage(QWidget):
    def __init__(self, session_manager: SessionManager, student_repo: StudentRepository, attendance_repo: AttendanceRepository, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.student_repo = student_repo
        self.attendance_repo = attendance_repo
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 16, 20, 16)
        self.layout.setSpacing(14)

        # Header Section
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 18px; font-weight: 700; color: #F0F6FC; letter-spacing: -0.2px;")
        
        subtitle = QLabel("Biometric attendance metrics and active session state")
        subtitle.setStyleSheet("font-size: 12px; color: #8B949E;")

        title_box.addWidget(header)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

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

        self.layout.addWidget(header_container)

        # Status Cards 2x2 Responsive Grid
        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)


        self.card_active_session = StatusCardWidget("Active Session", "None", "No session running")
        self.card_present = StatusCardWidget("Present Today", "0", "Students verified")
        self.card_absent = StatusCardWidget("Unverified", "0", "Students pending")
        self.card_total = StatusCardWidget("Total Directory", "0", "Enrolled students")

        cards_layout.addWidget(self.card_active_session, 0, 0)
        cards_layout.addWidget(self.card_present, 0, 1)
        cards_layout.addWidget(self.card_absent, 1, 0)
        cards_layout.addWidget(self.card_total, 1, 1)
        self.layout.addLayout(cards_layout)

        # Recent Attendance Section Header
        activity_header = QHBoxLayout()
        recent_label = QLabel("Recent Activity")
        recent_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F0F6FC;")
        
        activity_header.addWidget(recent_label)
        activity_header.addStretch()
        self.layout.addLayout(activity_header)

        # Attendance Table
        self.attendance_table = AttendanceTableWidget()
        self.layout.addWidget(self.attendance_table)

    def refresh(self):
        stats = self.session_manager.get_session_stats()
        total_students = len(self.student_repo.get_all(active_only=True))

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
            
            # Load active session records into table
            records = self.attendance_repo.get_session_attendance(stats["session_id"])
            self.attendance_table.set_data(records)
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
            self.card_active_session.set_value("None", "Standby")
            self.card_present.set_value("0", "0.0% verified")
            self.card_absent.set_value(str(total_students), f"{total_students} pending")
            self.attendance_table.set_data([])

        self.card_total.set_value(str(total_students), "Enrolled students")
