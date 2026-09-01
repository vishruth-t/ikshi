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
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # Header
        header = QLabel("DASHBOARD OVERVIEW")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #F8FAFC;")
        self.layout.addWidget(header)

        # Status Cards Grid
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.card_active_session = StatusCardWidget("Active Session", "None", "No session running", "#3B82F6")
        self.card_present = StatusCardWidget("Present Count", "0", "Students recognized today", "#10B981")
        self.card_absent = StatusCardWidget("Absent Count", "0", "Students absent", "#EF4444")
        self.card_total = StatusCardWidget("Total Enrolled", "0", "Active registered faces", "#8B5CF6")

        cards_layout.addWidget(self.card_active_session)
        cards_layout.addWidget(self.card_present)
        cards_layout.addWidget(self.card_absent)
        cards_layout.addWidget(self.card_total)
        self.layout.addLayout(cards_layout)

        # Recent Attendance Section
        recent_label = QLabel("Recent Attendance Activity")
        recent_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #CBD5E1;")
        self.layout.addWidget(recent_label)

        self.attendance_table = AttendanceTableWidget()
        self.layout.addWidget(self.attendance_table)

    def refresh(self):
        stats = self.session_manager.get_session_stats()
        total_students = len(self.student_repo.get_all(active_only=True))
        
        if stats["active"]:
            self.card_active_session.set_value(f"{stats['class_name']} - {stats['subject']}", f"Session ID #{stats['session_id']}")
            present = stats["present_count"]
            absent = max(0, total_students - present)
            self.card_present.set_value(str(present), f"{stats['attendance_percentage']:.1f}% Attendance")
            self.card_absent.set_value(str(absent), "Remaining enrolled")
            
            # Load current session records
            records = self.attendance_repo.get_session_attendance(stats["session_id"])
            self.attendance_table.set_data(records)
        else:
            self.card_active_session.set_value("No Session", "Start a session in Attendance tab")
            self.card_present.set_value("0", "0% Attendance")
            self.card_absent.set_value(str(total_students), "All students")
            self.attendance_table.set_data([])

        self.card_total.set_value(str(total_students), "Registered in database")
