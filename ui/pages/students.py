from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QComboBox
)
from PySide6.QtCore import Slot, Signal
from ui.widgets.student_table import StudentTableWidget
from database.repositories import StudentRepository
from database.models import Student
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS

class StudentsPage(QWidget):
    request_re_enroll = Signal(object) # emits Student object

    def __init__(self, student_repo: StudentRepository, parent=None):
        super().__init__(parent)
        self.student_repo = student_repo
        self.all_students = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Header Row with Stat Badges
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Student Directory")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #F0F6FC; letter-spacing: -0.2px;")
        
        subtitle = QLabel("Manage enrolled students and biometric profiles")
        subtitle.setStyleSheet("font-size: 12px; color: #8B949E;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.counter_badge = QLabel("0 Students")
        self.counter_badge.setStyleSheet("""
            background-color: #21262D;
            color: #8B949E;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_row.addWidget(self.counter_badge)
        layout.addLayout(header_row)

        # Search and Filter Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(8)

        input_style = """
            QLineEdit, QComboBox {
                background-color: #0D1117;
                color: #F0F6FC;
                border: 1px solid #30363D;
                padding: 7px 10px;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #cba6f7;
            }

        """

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or student ID...")
        self.search_input.setStyleSheet(input_style)
        self.search_input.textChanged.connect(self.filter_students)
        toolbar_layout.addWidget(self.search_input, stretch=3)

        # Department Filter Dropdown
        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments")
        self.dept_filter.addItems(DEFAULT_DEPARTMENTS)
        self.dept_filter.setStyleSheet(input_style)
        self.dept_filter.currentIndexChanged.connect(self.filter_students)
        toolbar_layout.addWidget(self.dept_filter, stretch=2)

        # Academic Year Filter Dropdown
        self.year_filter = QComboBox()
        self.year_filter.addItem("All Academic Years")
        self.year_filter.addItems(DEFAULT_ACADEMIC_YEARS)
        self.year_filter.setStyleSheet(input_style)
        self.year_filter.currentIndexChanged.connect(self.filter_students)
        toolbar_layout.addWidget(self.year_filter, stretch=2)

        btn_clear = QPushButton("Reset")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #C9D1D9;
                border: 1px solid #30363D;
                padding: 7px 12px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #30363D;
                color: white;
            }
        """)
        btn_clear.clicked.connect(self._reset_filters)
        toolbar_layout.addWidget(btn_clear)

        layout.addWidget(toolbar)

        # Student Table
        self.student_table = StudentTableWidget()
        self.student_table.toggle_active_signal.connect(self.toggle_student_status)
        self.student_table.re_enroll_signal.connect(self.handle_re_enroll)
        self.student_table.delete_signal.connect(self.handle_delete)
        layout.addWidget(self.student_table, stretch=1)

    def _reset_filters(self):
        self.search_input.clear()
        self.dept_filter.setCurrentIndex(0)
        self.year_filter.setCurrentIndex(0)
        self.filter_students()

    def refresh(self):
        students = self.student_repo.get_all(active_only=False)
        self.all_students = students
        active_cnt = sum(1 for s in students if s.active)
        self.counter_badge.setText(f"{len(students)} Total • {active_cnt} Active")
        self.filter_students()

    def filter_students(self):
        text = self.search_input.text().lower().strip()
        dept = self.dept_filter.currentText()
        year = self.year_filter.currentText()

        filtered = self.all_students

        if text:
            filtered = [
                s for s in filtered
                if text in s.name.lower() or text in s.student_number.lower()
            ]

        if dept and dept != "All Departments":
            filtered = [s for s in filtered if s.department == dept]

        if year and year != "All Academic Years":
            filtered = [s for s in filtered if s.year == year]

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
            f"Are you sure you want to permanently delete '{student_name}' (ID: {student_id})?\n\nThis will remove their profile and past attendance records.",
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



