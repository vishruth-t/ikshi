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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("ATTENDANCE REPORTS & CSV EXPORT")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(title)

        # Filters Box
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setSpacing(10)

        # Row 1: Text Filters & Date Checkbox
        row1 = QHBoxLayout()
        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("Filter Class (e.g. CS-101)")

        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("Filter Subject")

        for f in [self.input_class, self.input_subject]:
            f.setStyleSheet("background-color: #0F172A; color: white; border: 1px solid #334155; padding: 8px; border-radius: 6px;")

        self.chk_date = QCheckBox("Filter by Date Range")
        self.chk_date.setStyleSheet("color: #CBD5E1; font-weight: bold;")
        self.chk_date.toggled.connect(self._toggle_date_inputs)

        row1.addWidget(self.input_class)
        row1.addWidget(self.input_subject)
        row1.addWidget(self.chk_date)
        filter_layout.addLayout(row1)

        # Row 2: Date Pickers & Action Buttons
        row2 = QHBoxLayout()
        lbl_from = QLabel("From:")
        lbl_from.setStyleSheet("color: #94A3B8;")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setStyleSheet("background-color: #0F172A; color: white; border: 1px solid #334155; padding: 6px; border-radius: 6px;")
        self.date_from.setEnabled(False)

        lbl_to = QLabel("To:")
        lbl_to.setStyleSheet("color: #94A3B8;")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setStyleSheet("background-color: #0F172A; color: white; border: 1px solid #334155; padding: 6px; border-radius: 6px;")
        self.date_to.setEnabled(False)

        btn_filter = QPushButton("🔍 Apply Filters")
        btn_filter.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 15px; border-radius: 6px;")
        btn_filter.clicked.connect(self.refresh)

        btn_clear = QPushButton("↺ Clear Filters")
        btn_clear.setStyleSheet("background-color: #475569; color: white; font-weight: bold; padding: 8px 15px; border-radius: 6px;")
        btn_clear.clicked.connect(self.clear_filters)

        btn_export = QPushButton("📥 Export to CSV")
        btn_export.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 8px 15px; border-radius: 6px;")
        btn_export.clicked.connect(self.export_csv)

        row2.addWidget(lbl_from)
        row2.addWidget(self.date_from)
        row2.addWidget(lbl_to)
        row2.addWidget(self.date_to)
        row2.addWidget(btn_filter)
        row2.addWidget(btn_clear)
        row2.addWidget(btn_export)
        filter_layout.addLayout(row2)

        layout.addWidget(filter_frame)

        # Counter Label
        self.counter_label = QLabel("Showing 0 records")
        self.counter_label.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.counter_label)

        # Attendance Table
        self.table = ReportsTableWidget()
        layout.addWidget(self.table)

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
        self.counter_label.setText(f"Found {len(data)} attendance record(s)")

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

