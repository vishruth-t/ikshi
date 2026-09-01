from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from typing import List
from database.models import Student

class StudentTableWidget(QTableWidget):
    toggle_active_signal = Signal(int, bool) # (student_id, current_active_status)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(["ID", "Student Number", "Name", "Department", "Year", "Status", "Actions"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1E293B;
                color: #F8FAFC;
                gridline-color: #334155;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #0F172A;
                color: #94A3B8;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

    def set_students(self, students: List[Student]):
        self.setRowCount(0)
        for row_idx, s in enumerate(students):
            self.insertRow(row_idx)
            self.setItem(row_idx, 0, QTableWidgetItem(str(s.id)))
            self.setItem(row_idx, 1, QTableWidgetItem(s.student_number))
            self.setItem(row_idx, 2, QTableWidgetItem(s.name))
            self.setItem(row_idx, 3, QTableWidgetItem(s.department))
            self.setItem(row_idx, 4, QTableWidgetItem(s.year))

            status_item = QTableWidgetItem("Active" if s.active else "Disabled")
            status_item.setForeground(Qt.green if s.active else Qt.red)
            self.setItem(row_idx, 5, status_item)

            # Action button
            action_btn = QPushButton("Disable" if s.active else "Enable")
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #334155;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #475569;
                }
            """)
            action_btn.clicked.connect(lambda _, st_id=s.id, act=s.active: self.toggle_active_signal.emit(st_id, act))
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.addWidget(action_btn)
            self.setCellWidget(row_idx, 6, btn_container)
