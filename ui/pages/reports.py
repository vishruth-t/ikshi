from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QMessageBox, QDateEdit, QCheckBox, QFrame
)
from PySide6.QtCore import QDate, Qt
import logging
from ui.widgets.attendance_table import ReportsTableWidget
from database.repositories import AttendanceRepository
from reports.exporter import AttendanceExporter
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS

logger = logging.getLogger(__name__)

class ReportsPage(QWidget):
    def __init__(self, attendance_repo: AttendanceRepository, parent=None):
        super().__init__(parent)
        self.attendance_repo = attendance_repo
        self.current_report_data = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Header Row
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Reports & Export")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #F0F6FC; letter-spacing: -0.2px;")
        
        subtitle = QLabel("Filter session logs and export attendance reports")
        subtitle.setStyleSheet("font-size: 12px; color: #8B949E;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.counter_badge = QLabel("0 Records")
        self.counter_badge.setStyleSheet("""
            background-color: #21262D;
            color: #8B949E;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_row.addWidget(self.counter_badge)

        btn_export = QPushButton("Export CSV")
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 6px;
                border: 1px solid #2EA043;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
        """)
        btn_export.clicked.connect(self.export_csv)
        header_row.addWidget(btn_export)

        layout.addLayout(header_row)

        # Filters Card
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(10)

        input_style = """
            QLineEdit, QComboBox, QDateEdit {
                background-color: #0D1117;
                color: #F0F6FC;
                border: 1px solid #30363D;
                padding: 7px 10px;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QComboBox:on, QDateEdit:focus {
                border: 1px solid #cba6f7;
            }
            QComboBox QAbstractItemView {
                background-color: #161B22;
                color: #F0F6FC;
                selection-background-color: #cba6f7;
                selection-color: #11111B;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 4px;
                outline: 0;
            }
            QComboBox QAbstractItemView::item {
                min-height: 26px;
                padding: 4px 8px;
                color: #F0F6FC;
                background-color: transparent;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #21262D;
                color: #F0F6FC;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #cba6f7;
                color: #11111B;
                font-weight: 600;
            }
        """


        # Row 1: Dropdown Filters & Text Filters
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments")
        self.dept_filter.addItems(DEFAULT_DEPARTMENTS)
        self.dept_filter.setStyleSheet(input_style)
        self.dept_filter.currentIndexChanged.connect(self.refresh)

        self.year_filter = QComboBox()
        self.year_filter.addItem("All Academic Years")
        self.year_filter.addItems(DEFAULT_ACADEMIC_YEARS)
        self.year_filter.setStyleSheet(input_style)
        self.year_filter.currentIndexChanged.connect(self.refresh)

        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("Filter Class (e.g. CS-101)")
        self.input_class.setStyleSheet(input_style)
        self.input_class.textChanged.connect(self.refresh)

        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("Filter Subject (e.g. Algorithms)")
        self.input_subject.setStyleSheet(input_style)
        self.input_subject.textChanged.connect(self.refresh)

        row1.addWidget(self.dept_filter, stretch=2)
        row1.addWidget(self.year_filter, stretch=2)
        row1.addWidget(self.input_class, stretch=2)
        row1.addWidget(self.input_subject, stretch=2)
        filter_layout.addLayout(row1)

        # Row 2: Date Range & Action Buttons
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.chk_date = QCheckBox("Filter Date Range")
        self.chk_date.setStyleSheet("color: #C9D1D9; font-weight: 500; font-size: 12px;")
        self.chk_date.toggled.connect(self._toggle_date_inputs)

        lbl_from = QLabel("From:")
        lbl_from.setStyleSheet("color: #8B949E; font-size: 12px; font-weight: 500;")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setStyleSheet(input_style)
        self.date_from.setEnabled(False)
        self.date_from.dateChanged.connect(self.refresh)

        lbl_to = QLabel("To:")
        lbl_to.setStyleSheet("color: #8B949E; font-size: 12px; font-weight: 500;")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setStyleSheet(input_style)
        self.date_to.setEnabled(False)
        self.date_to.dateChanged.connect(self.refresh)

        btn_filter = QPushButton("Apply Filters")
        btn_filter.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7;
                color: #11111B;
                font-weight: 700;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 6px;
                border: 1px solid #cba6f7;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        btn_filter.clicked.connect(self.refresh)


        btn_reset = QPushButton("Reset")
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #C9D1D9;
                border: 1px solid #30363D;
                padding: 7px 12px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #30363D;
                color: white;
            }
        """)
        btn_reset.clicked.connect(self._reset_filters)

        row2.addWidget(self.chk_date)
        row2.addWidget(lbl_from)
        row2.addWidget(self.date_from)
        row2.addWidget(lbl_to)
        row2.addWidget(self.date_to)
        row2.addStretch()
        row2.addWidget(btn_filter)
        row2.addWidget(btn_reset)
        filter_layout.addLayout(row2)

        layout.addWidget(filter_frame)

        # Reports Table
        self.reports_table = ReportsTableWidget()
        layout.addWidget(self.reports_table, stretch=1)

        # Initial Load
        self.refresh()

    def _toggle_date_inputs(self, checked: bool):
        self.date_from.setEnabled(checked)
        self.date_to.setEnabled(checked)
        self.refresh()

    def _reset_filters(self):
        self.dept_filter.setCurrentIndex(0)
        self.year_filter.setCurrentIndex(0)
        self.input_class.clear()
        self.input_subject.clear()
        self.chk_date.setChecked(False)
        self.refresh()

    def refresh(self):
        dept = self.dept_filter.currentText()
        year = self.year_filter.currentText()
        cls = self.input_class.text().strip() or None
        subj = self.input_subject.text().strip() or None
        start_date = None
        end_date = None

        if self.chk_date.isChecked():
            start_date = self.date_from.date().toString("yyyy-MM-dd")
            end_date = self.date_to.date().toString("yyyy-MM-dd")

        data = self.attendance_repo.get_report_data(
            start_date=start_date,
            end_date=end_date,
            class_name=cls,
            subject=subj,
            department=dept,
            year=year
        )
        self.current_report_data = data
        self.reports_table.set_data(data)
        self.counter_badge.setText(f"{len(data)} Records")

    def export_csv(self):
        # Refresh to ensure latest data is loaded according to active filters
        self.refresh()

        if not self.current_report_data:
            QMessageBox.warning(self, "Export Warning", "No attendance data matches the current filters to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Attendance Report",
            "attendance_report.csv",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if file_path:
            try:
                success = AttendanceExporter.export_to_csv(file_path, self.current_report_data)
                if success:
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Attendance report successfully exported ({len(self.current_report_data)} records) to:\n{file_path}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Export Failed",
                        "Unable to generate the attendance report file. Please check file permissions and try again."
                    )
            except Exception as e:
                logger.error(f"Error exporting report: {e}")
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"An error occurred while saving the report:\n{e}"
                )


