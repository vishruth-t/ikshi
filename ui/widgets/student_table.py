from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QWidget, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt, Signal
from typing import List
from database.models import Student
from ui.widgets.attendance_table import TABLE_STYLESHEET

def create_avatar_widget(name: str) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setSpacing(10)

    # Initials
    parts = name.strip().split()
    initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper() if parts else "ST"

    # Deterministic color for initial badge
    colors = ["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EC4899", "#06B6D4"]
    bg_color = colors[sum(ord(c) for c in name) % len(colors)]

    avatar = QLabel(initials)
    avatar.setFixedSize(30, 30)
    avatar.setAlignment(Qt.AlignCenter)
    avatar.setStyleSheet(f"""
        background-color: {bg_color}33;
        color: {bg_color};
        border: 1px solid {bg_color}88;
        border-radius: 15px;
        font-weight: 800;
        font-size: 11px;
    """)

    name_label = QLabel(name)
    name_label.setStyleSheet("color: #F8FAFC; font-weight: 600; font-size: 13px;")

    layout.addWidget(avatar)
    layout.addWidget(name_label)
    layout.addStretch()
    return container

def create_student_status_pill(active: bool) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setAlignment(Qt.AlignCenter)

    bg = "rgba(16, 185, 129, 0.15)" if active else "rgba(239, 68, 68, 0.15)"
    color = "#34D399" if active else "#F87171"
    border = "rgba(16, 185, 129, 0.3)" if active else "rgba(239, 68, 68, 0.3)"
    text = "● Active" if active else "● Disabled"

    pill = QLabel(text)
    pill.setStyleSheet(f"""
        background-color: {bg};
        color: {color};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 700;
    """)
    layout.addWidget(pill)
    return container


class StudentTableWidget(QTableWidget):
    toggle_active_signal = Signal(int, bool) # (student_id, current_active_status)
    re_enroll_signal = Signal(int) # (student_id)
    delete_signal = Signal(int, str) # (student_id, student_name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(["STUDENT ID", "STUDENT NAME", "DEPARTMENT", "YEAR", "STATUS", "ACTIONS"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet(TABLE_STYLESHEET)

    def set_students(self, students: List[Student]):
        self.setRowCount(0)
        for row_idx, s in enumerate(students):
            self.insertRow(row_idx)
            
            # Student Number
            id_item = QTableWidgetItem(s.student_number)
            id_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 0, id_item)

            # Name with Avatar
            self.setCellWidget(row_idx, 1, create_avatar_widget(s.name))

            # Department & Year
            dept_item = QTableWidgetItem(s.department)
            dept_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 2, dept_item)

            year_item = QTableWidgetItem(s.year)
            year_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 3, year_item)

            # Status Pill
            self.setCellWidget(row_idx, 4, create_student_status_pill(s.active))

            # Action buttons
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(8)

            # 1. Toggle Active Button
            toggle_btn = QPushButton("Disable" if s.active else "Enable")
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #94A3B8;
                    border: 1px solid #334155;
                    padding: 5px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #F8FAFC;
                }
            """)
            toggle_btn.clicked.connect(lambda _, st_id=s.id, act=s.active: self.toggle_active_signal.emit(st_id, act))
            btn_layout.addWidget(toggle_btn)

            # 2. Re-enroll Face Button
            reenroll_btn = QPushButton("📸 Re-Enroll")
            reenroll_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(59, 130, 246, 0.15);
                    color: #60A5FA;
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    padding: 5px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                    color: white;
                }
            """)
            reenroll_btn.clicked.connect(lambda _, st_id=s.id: self.re_enroll_signal.emit(st_id))
            btn_layout.addWidget(reenroll_btn)

            # 3. Delete Student Button
            delete_btn = QPushButton("🗑 Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(239, 68, 68, 0.15);
                    color: #F87171;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    padding: 5px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    color: white;
                }
            """)
            delete_btn.clicked.connect(lambda _, st_id=s.id, st_name=s.name: self.delete_signal.emit(st_id, st_name))
            btn_layout.addWidget(delete_btn)

            self.setCellWidget(row_idx, 5, btn_container)


