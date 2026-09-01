from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from typing import List, Dict, Any

TABLE_STYLESHEET = """
    QTableWidget {
        background-color: #111827;
        alternate-background-color: #0F172A;
        color: #F8FAFC;
        gridline-color: #1E293B;
        border: 1px solid #1E293B;
        border-radius: 12px;
        selection-background-color: #1E293B;
        selection-color: #F8FAFC;
        outline: none;
    }
    QHeaderView::section {
        background-color: #090D16;
        color: #94A3B8;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 10px 8px;
        border: none;
        border-bottom: 2px solid #1E293B;
    }
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #1E293B;
    }
    QScrollBar:vertical {
        background: #0B0F19;
        width: 8px;
        border-radius: 4px;
        margin: 2px;
    }
    QScrollBar::handle:vertical {
        background: #334155;
        min-height: 24px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #475569;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

def create_status_pill(status: str) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setAlignment(Qt.AlignCenter)
    
    is_present = status.lower() == "present"
    bg_color = "rgba(16, 185, 129, 0.15)" if is_present else "rgba(239, 68, 68, 0.15)"
    text_color = "#34D399" if is_present else "#F87171"
    border_color = "rgba(16, 185, 129, 0.3)" if is_present else "rgba(239, 68, 68, 0.3)"
    icon = "● "

    pill = QLabel(f"{icon}{status}")
    pill.setStyleSheet(f"""
        background-color: {bg_color};
        color: {text_color};
        border: 1px solid {border_color};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 700;
    """)
    layout.addWidget(pill)
    return container

def create_confidence_pill(score: float) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setAlignment(Qt.AlignCenter)

    pct = int(score * 100) if score <= 1.0 else int(score)
    color = "#38BDF8" if pct >= 70 else "#F59E0B"
    bg = "rgba(56, 189, 248, 0.12)" if pct >= 70 else "rgba(245, 158, 11, 0.12)"
    border = "rgba(56, 189, 248, 0.25)" if pct >= 70 else "rgba(245, 158, 11, 0.25)"

    pill = QLabel(f"{score:.2f} ({pct}%)")
    pill.setStyleSheet(f"""
        background-color: {bg};
        color: {color};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
    """)
    layout.addWidget(pill)
    return container


class AttendanceTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["STUDENT ID", "NAME", "TIME", "STATUS", "MATCH SCORE"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet(TABLE_STYLESHEET)

    def set_data(self, records: List[Dict[str, Any]]):
        self.setRowCount(0)
        for row_idx, r in enumerate(records):
            self.insertRow(row_idx)
            
            # Student ID
            id_item = QTableWidgetItem(r.get("student_number", ""))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(r.get("name", ""))
            self.setItem(row_idx, 1, name_item)
            
            # Timestamp (HH:MM:SS)
            raw_time = r.get("marked_at", "")
            display_time = raw_time.split("T")[-1][:8] if "T" in raw_time else raw_time
            time_item = QTableWidgetItem(display_time)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 2, time_item)
            
            # Status Pill Widget
            self.setCellWidget(row_idx, 3, create_status_pill(r.get("status", "Present")))

            # Confidence Pill Widget
            sim = float(r.get("similarity", 0.0))
            self.setCellWidget(row_idx, 4, create_confidence_pill(sim))


class ReportsTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels([
            "DATE", "CLASS", "SUBJECT", "STUDENT ID", "NAME", "DEPT", "TIME", "STATUS", "CONFIDENCE"
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet(TABLE_STYLESHEET)

    def set_data(self, records: List[Dict[str, Any]]):
        self.setRowCount(0)
        for row_idx, r in enumerate(records):
            self.insertRow(row_idx)
            
            # Date
            date_item = QTableWidgetItem(str(r.get("date", "")))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 0, date_item)

            # Class & Subject
            self.setItem(row_idx, 1, QTableWidgetItem(str(r.get("class_name", ""))))
            self.setItem(row_idx, 2, QTableWidgetItem(str(r.get("subject", ""))))
            
            # Student ID
            id_item = QTableWidgetItem(str(r.get("student_number", "")))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 3, id_item)

            # Name & Dept
            self.setItem(row_idx, 4, QTableWidgetItem(str(r.get("name", ""))))
            self.setItem(row_idx, 5, QTableWidgetItem(str(r.get("department", ""))))
            
            # Timestamp
            raw_time = str(r.get("marked_at", ""))
            display_time = raw_time.split("T")[-1][:8] if "T" in raw_time else raw_time
            time_item = QTableWidgetItem(display_time)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 6, time_item)
            
            # Status Pill
            self.setCellWidget(row_idx, 7, create_status_pill(str(r.get("status", "Present"))))

            # Confidence Pill
            sim = float(r.get("similarity", 0.0))
            self.setCellWidget(row_idx, 8, create_confidence_pill(sim))


