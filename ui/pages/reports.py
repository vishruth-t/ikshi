from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
)
from ui.widgets.attendance_table import AttendanceTableWidget
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
        filter_layout = QHBoxLayout()
        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("Filter Class (e.g. CS-101)")

        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("Filter Subject")

        for f in [self.input_class, self.input_subject]:
            f.setStyleSheet("background-color: #1E293B; color: white; border: 1px solid #334155; padding: 8px; border-radius: 6px;")

        btn_filter = QPushButton("🔍 Filter Reports")
        btn_filter.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 15px; border-radius: 6px;")
        btn_filter.clicked.connect(self.refresh)

        btn_export = QPushButton("📥 Export to CSV")
        btn_export.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 8px 15px; border-radius: 6px;")
        btn_export.clicked.connect(self.export_csv)

        filter_layout.addWidget(self.input_class)
        filter_layout.addWidget(self.input_subject)
        filter_layout.addWidget(btn_filter)
        filter_layout.addWidget(btn_export)
        layout.addLayout(filter_layout)

        # Attendance Table
        self.table = AttendanceTableWidget()
        layout.addWidget(self.table)

    def refresh(self):
        cls = self.input_class.text().strip() or None
        subj = self.input_subject.text().strip() or None
        data = self.attendance_repo.get_report_data(class_name=cls, subject=subj)
        self.current_report_data = data
        self.table.set_data(data)

    def export_csv(self):
        if not self.current_report_data:
            QMessageBox.warning(self, "Export Warning", "No attendance data available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Attendance CSV", "attendance_report.csv", "CSV Files (*.csv)")
        if file_path:
            success = AttendanceExporter.export_to_csv(file_path, self.current_report_data)
            if success:
                QMessageBox.information(self, "Export Success", f"Attendance report exported to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Export Error", "Failed to write CSV file.")
