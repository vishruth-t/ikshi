from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from typing import List, Dict, Any

TABLE_STYLESHEET = """
    QTableWidget {
        background-color: #0D1117;
        alternate-background-color: #161B22;
        color: #F0F6FC;
        gridline-color: transparent;
        border: 1px solid #30363D;
        border-radius: 6px;
        selection-background-color: #21262D;
        selection-color: #F0F6FC;
        outline: none;
    }
    QHeaderView::section {
        background-color: #161B22;
        color: #8B949E;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 10px 8px;
        border: none;
        border-bottom: 1px solid #30363D;
    }
    QTableWidget::item {
        padding: 6px 10px;
        border-bottom: 1px solid #21262D;
        color: #F0F6FC;
        font-size: 13px;
    }
    QScrollBar:vertical {
        background: #0D1117;
        width: 8px;
        border-radius: 4px;
        margin: 2px;
    }
    QScrollBar::handle:vertical {
        background: #30363D;
        min-height: 24px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #484F58;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

def create_status_pill(status: str) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setAlignment(Qt.AlignCenter)
    
    is_present = status.lower() == "present"
    bg = "#162B1D" if is_present else "#21262D"
    color = "#3FB950" if is_present else "#F85149"
    border = "#238636" if is_present else "#30363D"

    pill = QLabel(status)
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

def create_confidence_pill(score: float) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setAlignment(Qt.AlignCenter)

    pct = int(score * 100) if score <= 1.0 else int(score)
    color = "#cba6f7" if pct >= 70 else "#D29922"


    pill = QLabel(f"{score:.2f} ({pct}%)")
    pill.setStyleSheet(f"""
        background-color: #21262D;
        color: {color};
        border: 1px solid #30363D;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 500;
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
        self.verticalHeader().setDefaultSectionSize(52)
        self.setShowGrid(False)
        self.setStyleSheet(TABLE_STYLESHEET)

    def set_data(self, records: List[Dict[str, Any]]):
        self.setRowCount(0)
        for row_idx, r in enumerate(records):
            self.insertRow(row_idx)
            self.setRowHeight(row_idx, 52)
            
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
        self.verticalHeader().setDefaultSectionSize(52)
        self.setShowGrid(False)
        self.setStyleSheet(TABLE_STYLESHEET)

    def set_data(self, records: List[Dict[str, Any]]):
        self.setRowCount(0)
        for row_idx, r in enumerate(records):
            self.insertRow(row_idx)
            self.setRowHeight(row_idx, 52)

            
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


