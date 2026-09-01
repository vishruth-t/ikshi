from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QDateEdit, QCheckBox, QFrame
)
from PySide6.QtCore import QDate, Qt
from ui.widgets.attendance_table import ReportsTableWidget
from database.repositories import AttendanceRepository
from reports.exporter import AttendanceExporter

class ReportsPage(QWidget):
    def __init__(self, attendance_repo: AttendanceRepository, parent=None):
        super().__init__(parent)
        self.attendance_repo = attendance_repo
        self.current_report_data = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title = QLabel("ATTENDANCE AUDIT & REPORTS")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;")
        
        subtitle = QLabel("Filter session logs by date, class, and subject, and export audit-ready CSV reports")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.counter_badge = QLabel("0 RECORDS")
        self.counter_badge.setStyleSheet("""
            background-color: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 12px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 800;
        """)
        header_row.addWidget(self.counter_badge)

        btn_export = QPushButton("📥 Export CSV")
        btn_export.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                color: white;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
            }
        """)
        btn_export.clicked.connect(self.export_csv)
        header_row.addWidget(btn_export)

        layout.addLayout(header_row)

        # Filters Card
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #111827);
                border: 1px solid #334155;
                border-radius: 14px;
                padding: 8px;
            }
        """)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 14, 16, 14)
        filter_layout.setSpacing(12)

        input_style = """
            QLineEdit, QDateEdit {
                background-color: #090D16;
                color: #F8FAFC;
                border: 1px solid #334155;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QDateEdit:focus {
                border: 1px solid #3B82F6;
            }
        """

        # Row 1: Text Filters & Date Checkbox
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("Filter Class (e.g. CS-101)")
        self.input_class.setStyleSheet(input_style)

        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("Filter Subject (e.g. Computer Vision)")
        self.input_subject.setStyleSheet(input_style)

        self.chk_date = QCheckBox("Filter Date Range")
        self.chk_date.setStyleSheet("color: #E2E8F0; font-weight: 600; font-size: 12px;")
        self.chk_date.toggled.connect(self._toggle_date_inputs)

        row1.addWidget(self.input_class, stretch=2)
        row1.addWidget(self.input_subject, stretch=2)
        row1.addWidget(self.chk_date)
        filter_layout.addLayout(row1)

        # Row 2: Date Pickers & Action Buttons
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        lbl_from = QLabel("From:")
        lbl_from.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 600;")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setStyleSheet(input_style)
        self.date_from.setEnabled(False)

        lbl_to = QLabel("To:")
        lbl_to.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 600;")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setStyleSheet(input_style)
        self.date_to.setEnabled(False)

        btn_filter = QPushButton("🔍 Apply Filters")
        btn_filter.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                color: white;
                font-weight: 700;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
            }
        """)
        btn_filter.clicked.connect(self.refresh)

        btn_clear = QPushButton("↺ Clear")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                font-weight: 600;
                padding: 8px 14px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: white;
            }
        """)
        btn_clear.clicked.connect(self.clear_filters)

        row2.addWidget(lbl_from)
        row2.addWidget(self.date_from)
        row2.addWidget(lbl_to)
        row2.addWidget(self.date_to)
        row2.addStretch()
        row2.addWidget(btn_filter)
        row2.addWidget(btn_clear)
        filter_layout.addLayout(row2)

        layout.addWidget(filter_frame)

        # Reports Table
        self.table = ReportsTableWidget()
        layout.addWidget(self.table, stretch=1)

    def _toggle_date_inputs(self, checked: bool):
        self.date_from.setEnabled(checked)
        self.date_to.setEnabled(checked)

    def clear_filters(self):
        self.input_class.clear()

        self.input_subject.clear()
        self.chk_date.setChecked(False)
        self.refresh()

    def refresh(self):
        cls = self.input_class.text().strip() or None
        subj = self.input_subject.text().strip() or None
        start_date = None
        end_date = None

        if self.chk_date.isChecked():
            start_date = self.date_from.date().toString("yyyy-MM-dd")
            end_date = self.date_to.date().toString("yyyy-MM-dd")

        data = self.attendance_repo.get_report_data(
            start_date=start_date, end_date=end_date, class_name=cls, subject=subj
        )
        self.current_report_data = data
        self.table.set_data(data)
        self.counter_badge.setText(f"{len(data)} RECORDS")

    def export_csv(self):

        if not self.current_report_data:
            QMessageBox.warning(self, "Export Warning", "No attendance data available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Attendance CSV", "attendance_report.csv", "CSV Files (*.csv)")
        if file_path:
            success = AttendanceExporter.export_to_csv(file_path, self.current_report_data)
            if success:
                QMessageBox.information(self, "Export Success", f"Attendance report exported successfully ({len(self.current_report_data)} rows) to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Export Error", "Failed to write CSV file.")

