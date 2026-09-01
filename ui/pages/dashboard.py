from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
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
        self.layout.setContentsMargins(28, 24, 28, 24)
        self.layout.setSpacing(20)

        # Header Hero Section
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        
        header = QLabel("DASHBOARD OVERVIEW")
        header.setStyleSheet("font-size: 22px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;")
        
        subtitle = QLabel("Real-time biometric attendance metrics and session monitoring")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")

        title_box.addWidget(header)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()


        self.session_badge = QLabel("○ STANDBY")
        self.session_badge.setStyleSheet("""
            background-color: rgba(148, 163, 184, 0.12);
            color: #94A3B8;
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(self.session_badge)

        self.layout.addWidget(header_container)

        # Status Cards Grid
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.card_active_session = StatusCardWidget("Active Session", "None", "No session running", "#3B82F6", icon="⚡")
        self.card_present = StatusCardWidget("Present Today", "0", "Students verified", "#10B981", icon="✅")
        self.card_absent = StatusCardWidget("Unverified / Absent", "0", "Students pending", "#EF4444", icon="⏳")
        self.card_total = StatusCardWidget("Total Directory", "0", "Enrolled biometrics", "#8B5CF6", icon="👥")

        cards_layout.addWidget(self.card_active_session)
        cards_layout.addWidget(self.card_present)
        cards_layout.addWidget(self.card_absent)
        cards_layout.addWidget(self.card_total)
        self.layout.addLayout(cards_layout)

        # Recent Attendance Section Header
        activity_header = QHBoxLayout()
        recent_label = QLabel("Recent Attendance Activity")
        recent_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #F1F5F9;")
        
        activity_hint = QLabel("Auto-updates on recognition")
        activity_hint.setStyleSheet("font-size: 11px; color: #64748B;")

        activity_header.addWidget(recent_label)
        activity_header.addSpacing(10)
        activity_header.addWidget(activity_hint)
        activity_header.addStretch()
        self.layout.addLayout(activity_header)

        # Attendance Table
        self.attendance_table = AttendanceTableWidget()
        self.layout.addWidget(self.attendance_table)

    def refresh(self):
        stats = self.session_manager.get_session_stats()
        total_students = len(self.student_repo.get_all(active_only=True))
        
        if stats["active"]:
            self.session_badge.setText(f"● ACTIVE: {stats['class_name'].upper()}")
            self.session_badge.setStyleSheet("""
                background-color: rgba(16, 185, 129, 0.15);
                color: #34D399;
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 20px;
                padding: 6px 16px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            """)
            self.card_active_session.set_value(f"{stats['class_name']}", f"{stats['subject']} • ID #{stats['session_id']}")
            present = stats["present_count"]
            absent = max(0, total_students - present)
            self.card_present.set_value(str(present), f"{stats['attendance_percentage']:.1f}% Verified")
            self.card_absent.set_value(str(absent), f"{absent} remaining students")
            
            # Load current session records
            records = self.attendance_repo.get_session_attendance(stats["session_id"])
            self.attendance_table.set_data(records)
        else:
            self.session_badge.setText("○ STANDBY")
            self.session_badge.setStyleSheet("""
                background-color: rgba(148, 163, 184, 0.12);
                color: #94A3B8;
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 20px;
                padding: 6px 16px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            """)
            self.card_active_session.set_value("No Session", "Start in Live Attendance tab")
            self.card_present.set_value("0", "0% Verified")
            self.card_absent.set_value(str(total_students), f"All {total_students} enrolled")
            self.attendance_table.set_data([])

        self.card_total.set_value(str(total_students), "Registered in database")

