from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QComboBox
)
from PySide6.QtCore import Slot, Signal
from ui.widgets.student_table import StudentTableWidget
from database.repositories import StudentRepository
from database.models import Student

class StudentsPage(QWidget):
    request_re_enroll = Signal(object) # emits Student object

    def __init__(self, student_repo: StudentRepository, parent=None):
        super().__init__(parent)
        self.student_repo = student_repo
        self.all_students = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header Row with Live Stat Badges
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title = QLabel("STUDENT MANAGEMENT DIRECTORY")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;")
        
        subtitle = QLabel("Manage biometric enrollment status, re-enroll faces, and audit records")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.counter_badge = QLabel("TOTAL: 0 ENROLLED")
        self.counter_badge.setStyleSheet("""
            background-color: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 12px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.5px;
        """)
        header_row.addWidget(self.counter_badge)
        layout.addLayout(header_row)

        # Search and Filter Toolbar Card
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 12px;
                padding: 4px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by student name, ID number, department...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #090D16;
                color: #F8FAFC;
                border: 1px solid #334155;
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
        self.search_input.textChanged.connect(self.filter_students)
        toolbar_layout.addWidget(self.search_input, stretch=3)

        btn_clear = QPushButton("Clear")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                padding: 8px 14px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: white;
            }
        """)
        btn_clear.clicked.connect(lambda: self.search_input.clear())
        toolbar_layout.addWidget(btn_clear)

        layout.addWidget(toolbar)

        # Student Table
        self.student_table = StudentTableWidget()
        self.student_table.toggle_active_signal.connect(self.toggle_student_status)
        self.student_table.re_enroll_signal.connect(self.handle_re_enroll)
        self.student_table.delete_signal.connect(self.handle_delete)
        layout.addWidget(self.student_table, stretch=1)

    def refresh(self):
        students = self.student_repo.get_all(active_only=False)
        self.all_students = students
        active_cnt = sum(1 for s in students if s.active)
        self.counter_badge.setText(f"TOTAL: {len(students)}  |  ACTIVE: {active_cnt}")
        self.filter_students(self.search_input.text())

    def filter_students(self, text: str):
        text = text.lower().strip()
        if not text:
            self.student_table.set_students(self.all_students)
            return

        filtered = [
            s for s in self.all_students
            if text in s.name.lower() or text in s.student_number.lower() or text in s.department.lower()
        ]
        self.student_table.set_students(filtered)

    @Slot(int, bool)
    def toggle_student_status(self, student_id: int, current_active: bool):
        self.student_repo.set_active(student_id, not current_active)
        self.refresh()

    @Slot(int)
    def handle_re_enroll(self, student_id: int):
        student = self.student_repo.get_by_id(student_id)
        if student:
            self.request_re_enroll.emit(student)

    @Slot(int, str)
    def handle_delete(self, student_id: int, student_name: str):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to permanently delete '{student_name}' (ID: {student_id})?\n\nThis will remove their 128D SFace biometric templates and past attendance records.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success = self.student_repo.delete(student_id)
            if success:
                QMessageBox.information(self, "Student Deleted", f"Student '{student_name}' was successfully removed.")
                self.refresh()
            else:
                QMessageBox.critical(self, "Delete Failed", "Failed to delete student from database.")


