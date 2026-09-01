from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from typing import List, Dict, Any

class AttendanceTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Student ID", "Name", "Time Marked", "Status", "Confidence"])
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
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #334155;
            }
        """)

    def set_data(self, records: List[Dict[str, Any]]):
        self.setRowCount(0)
        for row_idx, r in enumerate(records):
            self.insertRow(row_idx)
            self.setItem(row_idx, 0, QTableWidgetItem(r.get("student_number", "")))
            self.setItem(row_idx, 1, QTableWidgetItem(r.get("name", "")))
            
            # Format timestamp to HH:MM:SS
            raw_time = r.get("marked_at", "")
            display_time = raw_time.split("T")[-1][:8] if "T" in raw_time else raw_time
            self.setItem(row_idx, 2, QTableWidgetItem(display_time))
            
            status_item = QTableWidgetItem(r.get("status", "Present"))
            status_item.setForeground(Qt.green)
            self.setItem(row_idx, 3, status_item)

            sim = r.get("similarity", 0.0)
            self.setItem(row_idx, 4, QTableWidgetItem(f"{sim:.2f}"))
