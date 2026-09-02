from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
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



from ui.utils.theme import get_table_qss
from config.settings import settings

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
        self.apply_theme()

    def apply_theme(self, theme_name: str = None):
        theme = theme_name or getattr(settings, "theme", "dark")
        self.setStyleSheet(get_table_qss(theme))

    def set_data(self, records: List[Dict[str, Any]]):
        self.setRowCount(0)
        for row_idx, r in enumerate(records):
            self.insertRow(row_idx)
            self.setRowHeight(row_idx, 52)
            
            # Student ID
            id_item = QTableWidgetItem(r.get("student_number", ""))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 0, id_item)
            
            # Name with Avatar
            from ui.widgets.student_table import create_avatar_widget
            self.setCellWidget(row_idx, 1, create_avatar_widget(r.get("name", ""), r.get("student_number", "")))
            
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
        self.apply_theme()

    def apply_theme(self, theme_name: str = None):
        theme = theme_name or getattr(settings, "theme", "dark")
        self.setStyleSheet(get_table_qss(theme))

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


class SecurityAuditsTableWidget(QTableWidget):
    inspect_evidence_signal = Signal(dict) # Emits audit record dictionary

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "TIMESTAMP", "SUSPECTED STUDENT", "DEPARTMENT", "SPOOF THREAT / REASON", "LIVENESS SCORE", "EVIDENCE"
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.setColumnWidth(0, 150)
        self.setColumnWidth(5, 140)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(52)
        self.setShowGrid(False)
        self.apply_theme()

    def apply_theme(self, theme_name: str = None):
        theme = theme_name or getattr(settings, "theme", "dark")
        self.setStyleSheet(get_table_qss(theme))

    def set_audits(self, audits: List[Dict[str, Any]]):
        self.setRowCount(0)
        for row_idx, a in enumerate(audits):
            self.insertRow(row_idx)
            self.setRowHeight(row_idx, 52)

            # 0. Timestamp
            raw_time = str(a.get("timestamp", ""))
            display_time = raw_time.replace("T", " ")[:19]
            ts_item = QTableWidgetItem(display_time)
            ts_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 0, ts_item)

            # 1. Suspected Student
            name = a.get("matched_name") or "Unknown"
            num = a.get("student_number")
            stu_str = f"{name} ({num})" if num else name
            self.setItem(row_idx, 1, QTableWidgetItem(stu_str))

            # 2. Department
            dept = a.get("department") or "N/A"
            dept_item = QTableWidgetItem(dept)
            dept_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 2, dept_item)

            # 3. Spoof Threat / Reason Pill
            reason = a.get("reason", "Spoof Detected")
            reason_item = QTableWidgetItem(reason)
            reason_item.setForeground(Qt.GlobalColor.yellow)
            self.setItem(row_idx, 3, reason_item)

            # 4. Liveness Score
            lscore = float(a.get("liveness_score", 0.0))
            score_container = QWidget()
            s_layout = QHBoxLayout(score_container)
            s_layout.setContentsMargins(4, 4, 4, 4)
            s_layout.setAlignment(Qt.AlignCenter)
            s_pill = QLabel(f"{int(lscore * 100)}% Live (FAIL)")
            s_pill.setStyleSheet("""
                background-color: #2D1515;
                color: #F85149;
                border: 1px solid #DA3633;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
            """)
            s_layout.addWidget(s_pill)
            self.setCellWidget(row_idx, 4, score_container)

            # 5. Evidence Action Button
            btn_container = QWidget()
            b_layout = QHBoxLayout(btn_container)
            b_layout.setContentsMargins(4, 4, 4, 4)
            b_layout.setAlignment(Qt.AlignCenter)

            has_snap = bool(a.get("snapshot_path") or a.get("ir_snapshot_path"))
            btn_inspect = QPushButton("Inspect Snapshots" if has_snap else "View Metrics")
            btn_inspect.setStyleSheet("""
                QPushButton {
                    background-color: #21262D;
                    color: #cba6f7;
                    border: 1px solid #30363D;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #30363D;
                    border-color: #cba6f7;
                }
            """)
            btn_inspect.clicked.connect(lambda _, audit=a: self.inspect_evidence_signal.emit(audit))
            b_layout.addWidget(btn_inspect)
            self.setCellWidget(row_idx, 5, btn_container)



