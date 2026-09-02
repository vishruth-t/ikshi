import os
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QWidget, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon
from typing import List
from database.models import Student
from ui.widgets.attendance_table import TABLE_STYLESHEET
from config.settings import settings

from ui.utils.avatar import render_circular_avatar

def create_avatar_widget(name: str, student_number: str = "") -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(6, 4, 6, 4)
    layout.setSpacing(10)
    layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    # Check for photo avatar in data/avatars/
    avatar_dir = os.path.join(settings.BASE_DIR, "data", "avatars")
    avatar_path = os.path.join(avatar_dir, f"{student_number}.jpg")
    has_photo = os.path.exists(avatar_path)

    avatar = QLabel()
    avatar.setFixedSize(34, 34)
    avatar.setAlignment(Qt.AlignCenter)

    if has_photo:
        pix = render_circular_avatar(avatar_path, size=34, border_color="#cba6f7", border_width=1.2)
        if not pix.isNull():
            avatar.setPixmap(pix)
            avatar.setStyleSheet("background: transparent; border: none;")
        else:
            has_photo = False

    if not has_photo:
        # Fallback to initials
        parts = name.strip().split()
        initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper() if parts else "ST"
        avatar.setText(initials)
        avatar.setStyleSheet("""
            background-color: #21262D;
            color: #cba6f7;
            border: 1px solid #30363D;
            border-radius: 17px;
            font-weight: 700;
            font-size: 11px;
        """)

    name_label = QLabel(name)
    name_label.setStyleSheet("font-weight: 600; font-size: 13px; border: none; background: transparent;")

    layout.addWidget(avatar)
    layout.addWidget(name_label)
    layout.addStretch()
    return container

def create_student_status_pill(active: bool) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setAlignment(Qt.AlignCenter)

    if active:
        bg = "#162B1D"
        color = "#3FB950"
        border = "#238636"
        text = "Active"
    else:
        bg = "#21262D"
        color = "#8B949E"
        border = "#30363D"
        text = "Inactive"

    pill = QLabel(text)
    pill.setStyleSheet(f"""
        background-color: {bg};
        color: {color};
        border: 1px solid {border};
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
    """)
    layout.addWidget(pill)
    return container


class StudentTableWidget(QTableWidget):
    toggle_active_signal = Signal(int, bool) # (student_id, current_active_status)
    re_enroll_signal = Signal(int) # (student_id)
    view_profile_signal = Signal(int) # (student_id)
    delete_signal = Signal(int, str) # (student_id, student_name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(["STUDENT ID", "STUDENT NAME", "DEPARTMENT", "YEAR", "STATUS", "ACTIONS"])
        
        # Column Width Allocation
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive) # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)     # Name + Avatar
        header.setSectionResizeMode(2, QHeaderView.Interactive) # Dept
        header.setSectionResizeMode(3, QHeaderView.Interactive) # Year
        header.setSectionResizeMode(4, QHeaderView.Interactive) # Status
        header.setSectionResizeMode(5, QHeaderView.Fixed)       # Actions

        self.setColumnWidth(0, 130)
        self.setColumnWidth(2, 130)
        self.setColumnWidth(3, 80)
        self.setColumnWidth(4, 100)
        self.setColumnWidth(5, 270)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(48)
        self.setShowGrid(False)
        self.apply_theme()

    def apply_theme(self, theme_name: str = None):
        from ui.utils.theme import get_table_qss
        theme = theme_name or getattr(settings, "theme", "dark")
        self.setStyleSheet(get_table_qss(theme))

    def set_students(self, students: List[Student]):
        self.setRowCount(0)
        for row_idx, s in enumerate(students):
            self.insertRow(row_idx)
            self.setRowHeight(row_idx, 48)
            
            # 0. Student Number / ID
            id_item = QTableWidgetItem(s.student_number)
            id_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 0, id_item)

            # 1. Student Name with Avatar
            self.setCellWidget(row_idx, 1, create_avatar_widget(s.name, s.student_number))

            # 2. Department
            dept_item = QTableWidgetItem(s.department)
            dept_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 2, dept_item)

            # 3. Year
            year_item = QTableWidgetItem(s.year)
            year_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 3, year_item)

            # 4. Status Pill
            self.setCellWidget(row_idx, 4, create_student_status_pill(s.active))

            # 5. Actions Panel
            action_container = QWidget()
            action_layout = QHBoxLayout(action_container)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(6)
            action_layout.setAlignment(Qt.AlignCenter)

            # Action 1: View Biometric Profile
            btn_profile = QPushButton("Profile")
            btn_profile.setToolTip(f"View biometric profile for {s.name}")
            btn_profile.setStyleSheet("""
                QPushButton {
                    background-color: #21262D;
                    color: #58A6FF;
                    border: 1px solid #30363D;
                    padding: 5px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #30363D;
                    color: #79C0FF;
                }
            """)
            btn_profile.clicked.connect(lambda _, st_id=s.id: self.view_profile_signal.emit(st_id))

            # Action 2: Re-Enroll
            btn_reenroll = QPushButton("Re-Enroll")
            btn_reenroll.setToolTip(f"Re-capture face samples for {s.name}")
            btn_reenroll.setStyleSheet("""
                QPushButton {
                    background-color: #cba6f7;
                    color: #11111B;
                    border: 1px solid #cba6f7;
                    padding: 5px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #b4befe;
                }
            """)
            btn_reenroll.clicked.connect(lambda _, st_id=s.id: self.re_enroll_signal.emit(st_id))

            # Action 3: Toggle Status
            if s.active:
                btn_toggle = QPushButton("Disable")
                btn_toggle.setToolTip("Disable student attendance")
                btn_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #21262D;
                        color: #8B949E;
                        border: 1px solid #30363D;
                        padding: 5px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #30363D;
                        color: #F0F6FC;
                    }
                """)
            else:
                btn_toggle = QPushButton("Enable")
                btn_toggle.setToolTip("Enable student attendance")
                btn_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #238636;
                        color: white;
                        border: 1px solid #2EA043;
                        padding: 5px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #2EA043;
                    }
                """)
            btn_toggle.clicked.connect(lambda _, st_id=s.id, act=s.active: self.toggle_active_signal.emit(st_id, act))

            # Action 4: Delete
            btn_delete = QPushButton("Delete")
            btn_delete.setToolTip(f"Delete {s.name}")
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #21262D;
                    color: #F85149;
                    border: 1px solid #30363D;
                    padding: 5px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #DA3633;
                    color: white;
                }
            """)
            btn_delete.clicked.connect(lambda _, st_id=s.id, st_name=s.name: self.delete_signal.emit(st_id, st_name))

            action_layout.addWidget(btn_profile)
            action_layout.addWidget(btn_reenroll)
            action_layout.addWidget(btn_toggle)
            action_layout.addWidget(btn_delete)

            self.setCellWidget(row_idx, 5, action_container)




