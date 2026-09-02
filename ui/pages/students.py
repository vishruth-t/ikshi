import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QComboBox
)
from PySide6.QtCore import Slot, Signal, Qt
from ui.widgets.student_table import StudentTableWidget
from database.repositories import StudentRepository
from database.models import Student
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS

class StudentsPage(QWidget):
    request_re_enroll = Signal(object) # emits Student object
    student_deleted = Signal(int)

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

        self.title_label = QLabel("Student Directory")
        self.subtitle = QLabel("Manage enrolled students and biometric profiles")

        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.counter_badge = QLabel("0 Students")
        header_row.addWidget(self.counter_badge)
        layout.addLayout(header_row)

        # Search and Filter Toolbar
        self.toolbar = QFrame()
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or student ID...")
        self.search_input.textChanged.connect(self.filter_students)
        toolbar_layout.addWidget(self.search_input, stretch=3)

        # Department Filter Dropdown
        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments")
        self.dept_filter.addItems(DEFAULT_DEPARTMENTS)
        self.dept_filter.currentIndexChanged.connect(self.filter_students)
        toolbar_layout.addWidget(self.dept_filter, stretch=2)

        # Academic Year Filter Dropdown
        self.year_filter = QComboBox()
        self.year_filter.addItem("All Academic Years")
        self.year_filter.addItems(DEFAULT_ACADEMIC_YEARS)
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

        layout.addWidget(self.toolbar)

        # Student Table
        self.student_table = StudentTableWidget()
        self.student_table.toggle_active_signal.connect(self.toggle_student_status)
        self.student_table.re_enroll_signal.connect(self.handle_re_enroll)
        self.student_table.view_profile_signal.connect(self.show_student_profile)
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

    def apply_theme(self, theme_name: str = None):
        from ui.utils.theme import get_palette
        from config.settings import settings
        theme = theme_name or getattr(settings, "theme", "dark")
        p = get_palette(theme)

        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {p['text_primary']}; letter-spacing: -0.2px; background: transparent; border: none;")
        self.subtitle.setStyleSheet(f"font-size: 12px; color: {p['text_secondary']}; background: transparent; border: none;")
        self.counter_badge.setStyleSheet(f"background-color: {p['bg_card']}; color: {p['text_secondary']}; border: 1px solid {p['border']}; border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 600;")
        self.toolbar.setStyleSheet(f"background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 6px;")
        
        if hasattr(self, "student_table"):
            self.student_table.apply_theme(theme)

    @Slot(int)
    def show_student_profile(self, student_id: int):
        """Open rich student biometric profile dialog."""
        import os
        from PySide6.QtWidgets import QDialog, QGridLayout
        from PySide6.QtGui import QPixmap
        from config.settings import settings

        student = self.student_repo.get_by_id(student_id)
        if not student:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Biometric Profile • {student.name}")
        dialog.setFixedWidth(460)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 10px;
            }
            QLabel {
                color: #F0F6FC;
            }
        """)

        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(16)

        # Top Header Box with Avatar
        top_box = QHBoxLayout()
        top_box.setSpacing(16)

        avatar_dir = os.path.join(settings.BASE_DIR, "data", "avatars")
        avatar_path = os.path.join(avatar_dir, f"{student.student_number}.jpg")

        from ui.utils.avatar import render_circular_avatar

        avatar_lbl = QLabel()
        avatar_lbl.setFixedSize(80, 80)
        avatar_lbl.setAlignment(Qt.AlignCenter)
        if os.path.exists(avatar_path):
            px = render_circular_avatar(avatar_path, size=80, border_color="#cba6f7", border_width=2.0)
            if not px.isNull():
                avatar_lbl.setPixmap(px)
                avatar_lbl.setStyleSheet("background: transparent; border: none;")
            else:
                os.path.exists(avatar_path)
        else:
            parts = student.name.strip().split()
            initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper() if parts else "ST"
            avatar_lbl.setText(initials)
            avatar_lbl.setStyleSheet("border: 2px solid #30363D; border-radius: 40px; background: #21262D; color: #cba6f7; font-size: 24px; font-weight: 700;")

        top_box.addWidget(avatar_lbl)

        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(4)
        name_lbl = QLabel(student.name)
        name_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #F0F6FC;")
        id_lbl = QLabel(f"Student ID: {student.student_number}")
        id_lbl.setStyleSheet("font-size: 13px; color: #8B949E;")
        status_lbl = QLabel("Status: Active" if student.active else "Status: Inactive")
        status_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #3FB950;" if student.active else "font-size: 12px; font-weight: 600; color: #8B949E;")

        info_vbox.addWidget(name_lbl)
        info_vbox.addWidget(id_lbl)
        info_vbox.addWidget(status_lbl)
        top_box.addLayout(info_vbox)
        top_box.addStretch()

        d_layout.addLayout(top_box)

        # Details Grid Card
        grid_card = QFrame()
        grid_card.setStyleSheet("background-color: #0D1117; border: 1px solid #30363D; border-radius: 8px; padding: 12px;")
        grid = QGridLayout(grid_card)
        grid.setSpacing(10)

        grid.addWidget(QLabel("<b>Department:</b>"), 0, 0)
        grid.addWidget(QLabel(student.department), 0, 1)

        grid.addWidget(QLabel("<b>Academic Year:</b>"), 1, 0)
        grid.addWidget(QLabel(student.year), 1, 1)

        grid.addWidget(QLabel("<b>Enrolled On:</b>"), 2, 0)
        grid.addWidget(QLabel(student.created_at[:10] if student.created_at else "N/A"), 2, 1)

        # Query multi-angle embedding samples
        pose_names = {
            "frontal": "👤 Frontal",
            "center": "👤 Frontal",
            "left_20": "👈 Left Angle",
            "left": "👈 Left Angle",
            "right_20": "👉 Right Angle",
            "right": "👉 Right Angle",
            "tilt_up": "👆 Chin Up",
            "up": "👆 Chin Up",
            "smile_down": "😊 Smile/Down",
            "smile": "😊 Smile/Down"
        }
        with self.student_repo.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT model_name, COALESCE(pose_tag, 'frontal') AS pose_tag FROM face_embeddings WHERE student_id = ?", (student.id,))
            emb_rows = c.fetchall()
            emb_count = len(emb_rows)
            enrolled_poses = [pose_names.get(r["pose_tag"], r["pose_tag"]) for r in emb_rows if r["model_name"] == "SFace"]

        grid.addWidget(QLabel("<b>Biometric Samples:</b>"), 3, 0)
        grid.addWidget(QLabel(f"{emb_count} Enrolled Embeddings (Multi-Angle)"), 3, 1)

        if enrolled_poses:
            grid.addWidget(QLabel("<b>Trained Angles:</b>"), 4, 0)
            pose_str = ", ".join(enrolled_poses[:5])
            grid.addWidget(QLabel(pose_str), 4, 1)

        d_layout.addWidget(grid_card)

        # Actions
        btn_box = QHBoxLayout()
        btn_reenroll = QPushButton("Re-Enroll Face")
        btn_reenroll.setStyleSheet("background-color: #cba6f7; color: #11111B; font-weight: 700; padding: 6px 14px; border-radius: 6px;")
        btn_reenroll.clicked.connect(lambda: [dialog.accept(), self.handle_re_enroll(student.id)])

        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; padding: 6px 14px; border-radius: 6px;")
        btn_close.clicked.connect(dialog.accept)

        btn_box.addStretch()
        btn_box.addWidget(btn_reenroll)
        btn_box.addWidget(btn_close)
        d_layout.addLayout(btn_box)

        dialog.exec()

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
                self.student_deleted.emit(student_id)
                QMessageBox.information(self, "Student Deleted", f"Student '{student_name}' was successfully removed.")
                self.refresh()
            else:
                QMessageBox.critical(self, "Delete Failed", "Failed to delete student from database.")



