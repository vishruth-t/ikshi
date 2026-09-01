from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Slot
from ui.widgets.student_table import StudentTableWidget
from database.repositories import StudentRepository

class StudentsPage(QWidget):
    def __init__(self, student_repo: StudentRepository, parent=None):
        super().__init__(parent)
        self.student_repo = student_repo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("STUDENT MANAGEMENT DIRECTORY")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(title)

        # Search Bar
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by student name, ID or department...")
        self.search_input.setStyleSheet("background-color: #1E293B; color: white; border: 1px solid #334155; padding: 8px; border-radius: 6px;")
        self.search_input.textChanged.connect(self.filter_students)
        search_box.addWidget(self.search_input)
        layout.addLayout(search_box)

        # Student Table
        self.student_table = StudentTableWidget()
        self.student_table.toggle_active_signal.connect(self.toggle_student_status)
        layout.addWidget(self.student_table)

    def refresh(self):
        students = self.student_repo.get_all(active_only=False)
        self.all_students = students
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
