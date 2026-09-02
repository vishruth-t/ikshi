import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QFileDialog, QMessageBox, QDateEdit, QFrame, QButtonGroup, QStackedWidget, QDialog, QGridLayout, QRadioButton
)
from PySide6.QtCore import QDate, Qt, Slot, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
import logging
from ui.widgets.attendance_table import ReportsTableWidget, SecurityAuditsTableWidget
from database.repositories import AttendanceRepository, SecurityAuditRepository
from reports.exporter import AttendanceExporter
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS

logger = logging.getLogger(__name__)

class ReportsPage(QWidget):
    def __init__(self, attendance_repo: AttendanceRepository, parent=None):
        super().__init__(parent)
        self.attendance_repo = attendance_repo
        self.security_repo = SecurityAuditRepository(attendance_repo.db)
        self.current_report_data = []
        self.current_audits_data = []
        self.active_tab = "attendance" # "attendance" or "security"
        self.active_date_preset = "all" # "all", "today", "week", "month", "custom"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # -------------------------------------------------------------
        # 1. Header Row
        # -------------------------------------------------------------
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.title_label = QLabel("Reports & Analytics")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #F0F6FC; letter-spacing: -0.2px;")
        
        self.subtitle_label = QLabel("Filter session logs, inspect forensic audits, and export multi-format records")
        self.subtitle_label.setStyleSheet("font-size: 12px; color: #8B949E;")

        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # Tab Switcher Buttons (Attendance Logs vs Security Audits)
        self.tab_container = QFrame()
        self.tab_container.setStyleSheet("background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 2px;")
        tab_layout = QHBoxLayout(self.tab_container)
        tab_layout.setContentsMargins(2, 2, 2, 2)
        tab_layout.setSpacing(4)

        self.btn_tab_attendance = QPushButton("📋 Attendance Logs")
        self.btn_tab_attendance.setCursor(Qt.PointingHandCursor)
        self.btn_tab_attendance.setStyleSheet("background-color: #cba6f7; color: #11111B; font-weight: 700; font-size: 12px; padding: 6px 14px; border-radius: 4px; border: none;")
        self.btn_tab_attendance.clicked.connect(lambda: self._switch_tab("attendance"))

        self.btn_tab_security = QPushButton("🛡️ Security & Spoof Audits")
        self.btn_tab_security.setCursor(Qt.PointingHandCursor)
        self.btn_tab_security.setStyleSheet("background-color: transparent; color: #8B949E; font-weight: 500; font-size: 12px; padding: 6px 14px; border-radius: 4px; border: none;")
        self.btn_tab_security.clicked.connect(lambda: self._switch_tab("security"))

        tab_layout.addWidget(self.btn_tab_attendance)
        tab_layout.addWidget(self.btn_tab_security)
        header_row.addWidget(self.tab_container)

        self.counter_badge = QLabel("0 Records")
        self.counter_badge.setStyleSheet("""
            background-color: #21262D;
            color: #C9D1D9;
            border: 1px solid #30363D;
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_row.addWidget(self.counter_badge)

        self.btn_export = QPushButton("Export Report")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 16px;
                border-radius: 6px;
                border: 1px solid #2EA043;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
        """)
        self.btn_export.clicked.connect(self.export_report)
        header_row.addWidget(self.btn_export)

        self.btn_clear = QPushButton("Clear Reports")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #F85149;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 16px;
                border-radius: 6px;
                border: 1px solid #DA3633;
            }
            QPushButton:hover {
                background-color: #DA3633;
                color: #FFFFFF;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_action)
        header_row.addWidget(self.btn_clear)

        layout.addLayout(header_row)

        # -------------------------------------------------------------
        # 2. Filter Card (For Attendance view)
        # -------------------------------------------------------------
        self.filter_card = QFrame()
        self.filter_card.setStyleSheet("""
            QFrame#filter_card {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
            }
        """)
        self.filter_card.setObjectName("filter_card")

        filter_layout = QVBoxLayout(self.filter_card)
        filter_layout.setContentsMargins(14, 12, 14, 12)
        filter_layout.setSpacing(12)

        self.filter_labels = []
        # Row 1: Categorical Dropdowns and Text Filters
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(12)

        # 1. Department
        dept_box = QVBoxLayout()
        dept_box.setSpacing(4)
        lbl_dept = QLabel("DEPARTMENT")
        lbl_dept.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        self.filter_labels.append(lbl_dept)
        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments")
        self.dept_filter.addItems(DEFAULT_DEPARTMENTS)
        self.dept_filter.currentIndexChanged.connect(self.refresh)
        dept_box.addWidget(lbl_dept)
        dept_box.addWidget(self.dept_filter)
        row1_layout.addLayout(dept_box, stretch=2)

        # 2. Academic Year
        year_box = QVBoxLayout()
        year_box.setSpacing(4)
        lbl_year = QLabel("ACADEMIC YEAR")
        lbl_year.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        self.filter_labels.append(lbl_year)
        self.year_filter = QComboBox()
        self.year_filter.addItem("All Academic Years")
        self.year_filter.addItems(DEFAULT_ACADEMIC_YEARS)
        self.year_filter.currentIndexChanged.connect(self.refresh)
        year_box.addWidget(lbl_year)
        year_box.addWidget(self.year_filter)
        row1_layout.addLayout(year_box, stretch=2)

        # 3. Class / Batch
        class_box = QVBoxLayout()
        class_box.setSpacing(4)
        lbl_class = QLabel("CLASS / BATCH")
        lbl_class.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        self.filter_labels.append(lbl_class)
        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("e.g. CS-101")
        self.input_class.setClearButtonEnabled(True)
        self.input_class.textChanged.connect(self.refresh)
        class_box.addWidget(lbl_class)
        class_box.addWidget(self.input_class)
        row1_layout.addLayout(class_box, stretch=2)

        # 4. Subject
        subject_box = QVBoxLayout()
        subject_box.setSpacing(4)
        lbl_subject = QLabel("SUBJECT")
        lbl_subject.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        self.filter_labels.append(lbl_subject)
        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("e.g. Computer Vision")
        self.input_subject.setClearButtonEnabled(True)
        self.input_subject.textChanged.connect(self.refresh)
        subject_box.addWidget(lbl_subject)
        subject_box.addWidget(self.input_subject)
        row1_layout.addLayout(subject_box, stretch=2)

        filter_layout.addLayout(row1_layout)

        # Row 2: Date Presets & Custom Pickers
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(8)

        lbl_timeline = QLabel("TIMELINE:")
        lbl_timeline.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px; margin-right: 4px;")
        self.filter_labels.append(lbl_timeline)
        row2_layout.addWidget(lbl_timeline)

        self.preset_group = QButtonGroup(self)
        self.preset_group.setExclusive(True)

        self.btn_preset_all = self._create_preset_btn("All Time", "all", active=True)
        self.btn_preset_today = self._create_preset_btn("Today", "today")
        self.btn_preset_week = self._create_preset_btn("Past 7 Days", "week")
        self.btn_preset_month = self._create_preset_btn("Past 30 Days", "month")
        self.btn_preset_custom = self._create_preset_btn("Custom Range", "custom")

        row2_layout.addWidget(self.btn_preset_all)
        row2_layout.addWidget(self.btn_preset_today)
        row2_layout.addWidget(self.btn_preset_week)
        row2_layout.addWidget(self.btn_preset_month)
        row2_layout.addWidget(self.btn_preset_custom)

        # Custom date pickers container
        self.custom_date_container = QWidget()
        custom_date_layout = QHBoxLayout(self.custom_date_container)
        custom_date_layout.setContentsMargins(8, 0, 0, 0)
        custom_date_layout.setSpacing(8)

        lbl_from = QLabel("From:")
        lbl_from.setStyleSheet("font-size: 11px; color: #8B949E; font-weight: 600;")
        self.date_from = QDateEdit()
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.refresh)

        lbl_to = QLabel("To:")
        lbl_to.setStyleSheet("font-size: 11px; color: #8B949E; font-weight: 600;")
        self.date_to = QDateEdit()
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.refresh)

        custom_date_layout.addWidget(lbl_from)
        custom_date_layout.addWidget(self.date_from)
        custom_date_layout.addWidget(lbl_to)
        custom_date_layout.addWidget(self.date_to)

        self.custom_date_container.setVisible(False)
        row2_layout.addWidget(self.custom_date_container)
        row2_layout.addStretch()

        btn_reset = QPushButton("Reset Filters")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #C9D1D9;
                border: 1px solid #30363D;
                padding: 5px 12px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #30363D;
                color: white;
            }
        """)
        btn_reset.clicked.connect(self._reset_filters)
        row2_layout.addWidget(btn_reset)

        filter_layout.addLayout(row2_layout)
        layout.addWidget(self.filter_card)

        # -------------------------------------------------------------
        # 3. Stacked Table View
        # -------------------------------------------------------------
        self.views_stack = QStackedWidget()

        # View 0: Attendance Table
        self.reports_table = ReportsTableWidget()
        self.views_stack.addWidget(self.reports_table)

        # View 1: Security Audits Table
        self.audits_table = SecurityAuditsTableWidget()
        self.audits_table.inspect_evidence_signal.connect(self.show_spoof_evidence)
        self.views_stack.addWidget(self.audits_table)

        layout.addWidget(self.views_stack, stretch=1)

    def apply_theme(self, theme_name: str = None):
        from ui.utils.theme import get_palette
        from config.settings import settings
        theme = theme_name or getattr(settings, "theme", "dark")
        p = get_palette(theme)

        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {p['text_primary']}; letter-spacing: -0.2px; background: transparent; border: none;")
        self.subtitle_label.setStyleSheet(f"font-size: 12px; color: {p['text_secondary']}; background: transparent; border: none;")
        self.tab_container.setStyleSheet(f"background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 6px; padding: 2px;")
        self.counter_badge.setStyleSheet(f"background-color: {p['bg_card']}; color: {p['text_secondary']}; border: 1px solid {p['border']}; border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600;")
        self.filter_card.setStyleSheet(f"background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 8px; padding: 12px 14px;")

        for lbl in getattr(self, "filter_labels", []):
            lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {p['text_secondary']}; letter-spacing: 0.5px;")

        if hasattr(self, "reports_table"):
            self.reports_table.apply_theme(theme)
        if hasattr(self, "audits_table"):
            self.audits_table.apply_theme(theme)
        self._switch_tab(self.active_tab)

    def _switch_tab(self, tab_id: str):
        from ui.utils.theme import get_palette
        from config.settings import settings
        p = get_palette(getattr(settings, "theme", "dark"))
        self.active_tab = tab_id
        inactive = f"background-color: transparent; color: {p['text_secondary']}; font-weight: 500; font-size: 12px; padding: 6px 14px; border-radius: 4px; border: none;"
        if tab_id == "attendance":
            self.btn_tab_attendance.setStyleSheet("background-color: #cba6f7; color: #11111B; font-weight: 700; font-size: 12px; padding: 6px 14px; border-radius: 4px; border: none;")
            self.btn_tab_security.setStyleSheet(inactive)
            self.filter_card.setVisible(True)
            self.btn_export.setVisible(True)
            self.btn_clear.setText("Clear Reports")
            self.views_stack.setCurrentIndex(0)
        else:
            self.btn_tab_security.setStyleSheet("background-color: #F85149; color: white; font-weight: 700; font-size: 12px; padding: 6px 14px; border-radius: 4px; border: none;")
            self.btn_tab_attendance.setStyleSheet(inactive)
            self.filter_card.setVisible(False)
            self.btn_export.setVisible(False)
            self.btn_clear.setText("Clear Audits")
            self.views_stack.setCurrentIndex(1)
        self.refresh()

    def _create_preset_btn(self, text: str, preset_id: str, active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setObjectName(f"preset_{preset_id}")
        self._apply_preset_style(btn, active)
        btn.clicked.connect(lambda: self._select_date_preset(preset_id))
        self.preset_group.addButton(btn)
        return btn

    def _apply_preset_style(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #cba6f7;
                    color: #11111B;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 5px 12px;
                    border-radius: 6px;
                    border: 1px solid #cba6f7;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0D1117;
                    color: #8B949E;
                    font-weight: 500;
                    font-size: 11px;
                    padding: 5px 12px;
                    border-radius: 6px;
                    border: 1px solid #30363D;
                }
                QPushButton:hover {
                    background-color: #21262D;
                    color: #F0F6FC;
                    border: 1px solid #8B949E;
                }
            """)

    def _select_date_preset(self, preset_id: str):
        self.active_date_preset = preset_id
        today = QDate.currentDate()

        for btn in self.preset_group.buttons():
            is_active = (btn.objectName() == f"preset_{preset_id}")
            btn.setChecked(is_active)
            self._apply_preset_style(btn, is_active)

        if preset_id == "custom":
            self.custom_date_container.setVisible(True)
        else:
            self.custom_date_container.setVisible(False)
            if preset_id == "today":
                self.date_from.setDate(today)
                self.date_to.setDate(today)
            elif preset_id == "week":
                self.date_from.setDate(today.addDays(-7))
                self.date_to.setDate(today)
            elif preset_id == "month":
                self.date_from.setDate(today.addDays(-30))
                self.date_to.setDate(today)

        self.refresh()

    def _reset_filters(self):
        self.dept_filter.setCurrentIndex(0)
        self.year_filter.setCurrentIndex(0)
        self.input_class.clear()
        self.input_subject.clear()
        self._select_date_preset("all")

    def refresh(self):
        if self.active_tab == "attendance":
            dept = self.dept_filter.currentText()
            year = self.year_filter.currentText()
            cls = self.input_class.text().strip()
            subj = self.input_subject.text().strip()

            start_date = None
            end_date = None

            if self.active_date_preset != "all":
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
            count_str = f"{len(data)} Record{'s' if len(data) != 1 else ''}"
            self.counter_badge.setText(count_str)
        else:
            audits = self.security_repo.get_all_audits()
            self.current_audits_data = audits
            self.audits_table.set_audits(audits)
            count_str = f"{len(audits)} Spoof Interception{'s' if len(audits) != 1 else ''}"
            self.counter_badge.setText(count_str)

    def show_spoof_evidence(self, audit: dict):
        """Open forensic inspection modal displaying intercepted RGB and IR snapshots."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Forensic Security Evidence • #{audit.get('id', '')}")
        dialog.setFixedWidth(680)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 10px;
            }
            QLabel {
                color: #F0F6FC;
            }
        """)

        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(14)

        # Header Title
        h_box = QHBoxLayout()
        title_v = QVBoxLayout()
        t_lbl = QLabel(f"⚠️ {audit.get('reason', 'Spoof Attempt Intercepted')}")
        t_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #F85149;")
        s_lbl = QLabel(f"Timestamp: {audit.get('timestamp', '')} • Suspected Student: {audit.get('matched_name', 'Unknown')} ({audit.get('student_number', 'N/A')})")
        s_lbl.setStyleSheet("font-size: 12px; color: #8B949E;")
        title_v.addWidget(t_lbl)
        title_v.addWidget(s_lbl)
        h_box.addLayout(title_v)
        d_layout.addLayout(h_box)

        # Side-by-Side Dual Snapshots
        snap_row = QHBoxLayout()
        snap_row.setSpacing(12)

        # 1. RGB Snapshot Card
        rgb_v = QVBoxLayout()
        rgb_lbl_tag = QLabel("RGB CAMERA SNAPSHOT")
        rgb_lbl_tag.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        rgb_img = QLabel()
        rgb_img.setFixedSize(300, 220)
        rgb_img.setAlignment(Qt.AlignCenter)
        rgb_path = audit.get("snapshot_path")
        if rgb_path and os.path.exists(rgb_path):
            px = QPixmap(rgb_path)
            rgb_img.setPixmap(px.scaled(300, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            rgb_img.setStyleSheet("border: 1px solid #30363D; border-radius: 6px; background-color: #0D1117;")
        else:
            rgb_img.setText("No RGB snapshot captured")
            rgb_img.setStyleSheet("border: 1px dashed #30363D; border-radius: 6px; background-color: #0D1117; color: #8B949E;")
        rgb_v.addWidget(rgb_lbl_tag)
        rgb_v.addWidget(rgb_img)
        snap_row.addLayout(rgb_v)

        # 2. IR Sensor Snapshot Card
        ir_v = QVBoxLayout()
        ir_lbl_tag = QLabel("INFRARED (IR) SENSOR SNAPSHOT")
        ir_lbl_tag.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        ir_img = QLabel()
        ir_img.setFixedSize(300, 220)
        ir_img.setAlignment(Qt.AlignCenter)
        ir_path = audit.get("ir_snapshot_path")
        if ir_path and os.path.exists(ir_path):
            px_ir = QPixmap(ir_path)
            ir_img.setPixmap(px_ir.scaled(300, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ir_img.setStyleSheet("border: 1px solid #30363D; border-radius: 6px; background-color: #0D1117;")
        else:
            ir_img.setText("No IR snapshot captured")
            ir_img.setStyleSheet("border: 1px dashed #30363D; border-radius: 6px; background-color: #0D1117; color: #8B949E;")
        ir_v.addWidget(ir_lbl_tag)
        ir_v.addWidget(ir_img)
        snap_row.addLayout(ir_v)

        d_layout.addLayout(snap_row)

        # Forensic Biometric Metrics Breakdown Card
        m_card = QFrame()
        m_card.setStyleSheet("background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px; padding: 10px;")
        m_grid = QGridLayout(m_card)
        m_grid.setSpacing(8)

        m_grid.addWidget(QLabel("<b>Composite Liveness:</b>"), 0, 0)
        m_grid.addWidget(QLabel(f"{float(audit.get('liveness_score', 0.0)) * 100:.1f}% (Rejected)"), 0, 1)

        m_grid.addWidget(QLabel("<b>Texture Analysis:</b>"), 0, 2)
        m_grid.addWidget(QLabel(f"{float(audit.get('texture_score', 0.0)) * 100:.1f}%"), 0, 3)

        m_grid.addWidget(QLabel("<b>Planar Reflectance:</b>"), 1, 0)
        m_grid.addWidget(QLabel(f"{float(audit.get('reflectance_score', 0.0)) * 100:.1f}%"), 1, 1)

        m_grid.addWidget(QLabel("<b>Gradient Entropy:</b>"), 1, 2)
        m_grid.addWidget(QLabel(f"{float(audit.get('entropy_score', 0.0)):.2f}"), 1, 3)

        d_layout.addWidget(m_card)

        # Close button
        b_box = QHBoxLayout()
        b_close = QPushButton("Close")
        b_close.setStyleSheet("background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; padding: 6px 16px; border-radius: 6px; font-weight: 600;")
        b_close.clicked.connect(dialog.accept)
        b_box.addStretch()
        b_box.addWidget(b_close)
        d_layout.addLayout(b_box)

        dialog.exec()

    def export_report(self):
        """Open modern interactive export dialog offering Excel (.xls), Printable HTML (.html), and CSV (.csv)."""
        self.refresh()
        is_attendance = (self.active_tab == "attendance")
        data = self.current_report_data if is_attendance else self.current_audits_data
        
        if not data:
            QMessageBox.warning(
                self,
                "Export Warning",
                "No records available to export with the currently active filters."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Export Report • Select Format")
        dialog.setFixedWidth(520)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 10px;
            }
            QLabel {
                color: #F0F6FC;
            }
        """)

        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(22, 20, 22, 20)
        d_layout.setSpacing(16)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        exp_title = QLabel("📥 Export Report Records")
        exp_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F0F6FC;")
        
        type_str = "Attendance Records" if is_attendance else "Security & Spoof Audit Logs"
        exp_sub = QLabel(f"Choose your desired export format for {len(data)} {type_str}.")
        exp_sub.setStyleSheet("font-size: 12px; color: #8B949E;")
        title_box.addWidget(exp_title)
        title_box.addWidget(exp_sub)
        d_layout.addLayout(title_box)

        # Format Selection Cards
        format_vbox = QVBoxLayout()
        format_vbox.setSpacing(10)

        cards = []
        fmt_group = QButtonGroup(dialog)

        options = [
            (
                0,
                "📊 Microsoft Excel Spreadsheet (.xls)",
                "Formatted multi-column workbook with header metrics, compatible with MS Excel, LibreOffice Calc, and Google Sheets.",
                "#58A6FF"
            ),
            (
                1,
                "📄 Printable HTML / PDF Document (.html)",
                "High-resolution styled web report with summary KPI badges, ready for browser inspection and 1-click PDF printing (Ctrl+P).",
                "#cba6f7"
            ),
            (
                2,
                "📑 CSV Spreadsheet (.csv)",
                "Standard UTF-8 comma-separated values table optimized for raw data ingestion and spreadsheet tools.",
                "#3FB950"
            )
        ]

        def update_card_styles():
            for card_frame, r_btn, opt_color in cards:
                if r_btn.isChecked():
                    card_frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: #1A162B;
                            border: 1.5px solid {opt_color};
                            border-radius: 8px;
                            padding: 10px 14px;
                        }}
                    """)
                else:
                    card_frame.setStyleSheet("""
                        QFrame {
                            background-color: #0D1117;
                            border: 1px solid #30363D;
                            border-radius: 8px;
                            padding: 10px 14px;
                        }
                        QFrame:hover {
                            background-color: #161B22;
                            border: 1px solid #8B949E;
                        }
                    """)

        rb_excel = None
        rb_html = None
        rb_csv = None

        for opt_id, title_text, desc_text, color_accent in options:
            card_frame = QFrame()
            card_frame.setCursor(Qt.PointingHandCursor)
            c_layout = QVBoxLayout(card_frame)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setSpacing(4)

            rb = QRadioButton(title_text)
            rb.setStyleSheet(f"QRadioButton {{ color: {color_accent}; font-weight: 700; font-size: 13px; border: none; background: transparent; }}")
            if opt_id == 0:
                rb.setChecked(True)
                rb_excel = rb
            elif opt_id == 1:
                rb_html = rb
            else:
                rb_csv = rb

            desc_lbl = QLabel(desc_text)
            desc_lbl.setStyleSheet("color: #8B949E; font-size: 11px; margin-left: 20px; border: none; background: transparent;")
            desc_lbl.setWordWrap(True)

            c_layout.addWidget(rb)
            c_layout.addWidget(desc_lbl)

            fmt_group.addButton(rb, opt_id)
            cards.append((card_frame, rb, color_accent))

            def make_handler(target_rb):
                return lambda event: target_rb.setChecked(True)
            
            card_frame.mousePressEvent = make_handler(rb)
            rb.toggled.connect(lambda: update_card_styles())
            format_vbox.addWidget(card_frame)

        update_card_styles()
        d_layout.addLayout(format_vbox)

        # Output Path Row
        path_box = QVBoxLayout()
        path_box.setSpacing(4)
        lbl_dest = QLabel("SAVE DESTINATION:")
        lbl_dest.setStyleSheet("font-size: 10px; font-weight: 700; color: #8B949E; letter-spacing: 0.5px;")
        
        path_row = QHBoxLayout()
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        base_name = f"attendance_report_{today_str}" if is_attendance else f"security_audits_{today_str}"
        default_dir = os.path.expanduser("~/Downloads") if os.path.exists(os.path.expanduser("~/Downloads")) else os.path.expanduser("~")
        
        input_path = QLineEdit(os.path.join(default_dir, f"{base_name}.xls"))
        input_path.setStyleSheet("""
            QLineEdit {
                background-color: #0D1117;
                color: #F0F6FC;
                border: 1px solid #30363D;
                padding: 7px 10px;
                border-radius: 6px;
                font-size: 12px;
            }
        """)
        
        def update_extension():
            cur = input_path.text()
            base, _ = os.path.splitext(cur)
            if rb_excel.isChecked():
                input_path.setText(f"{base}.xls")
            elif rb_html.isChecked():
                input_path.setText(f"{base}.html")
            else:
                input_path.setText(f"{base}.csv")

        rb_excel.toggled.connect(update_extension)
        rb_html.toggled.connect(update_extension)
        rb_csv.toggled.connect(update_extension)

        btn_browse = QPushButton("Browse...")
        btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #F0F6FC;
                border: 1px solid #30363D;
                padding: 7px 14px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #30363D;
            }
        """)
        
        def do_browse():
            ext = ".xls" if rb_excel.isChecked() else (".html" if rb_html.isChecked() else ".csv")
            filt = "Excel Workbook (*.xls)" if rb_excel.isChecked() else ("HTML Document (*.html)" if rb_html.isChecked() else "CSV Spreadsheet (*.csv)")
            fpath, _ = QFileDialog.getSaveFileName(dialog, "Select Save Location", input_path.text(), f"{filt};;All Files (*.*)")
            if fpath:
                input_path.setText(fpath)

        btn_browse.clicked.connect(do_browse)
        path_row.addWidget(input_path, stretch=1)
        path_row.addWidget(btn_browse)
        path_box.addWidget(lbl_dest)
        path_box.addLayout(path_row)
        d_layout.addLayout(path_box)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; padding: 7px 16px; border-radius: 6px; font-weight: 500;")
        btn_cancel.clicked.connect(dialog.reject)

        btn_do_export = QPushButton("Export Report")
        btn_do_export.setStyleSheet("background-color: #238636; color: white; border: 1px solid #2EA043; padding: 7px 20px; border-radius: 6px; font-weight: 700;")
        
        def execute_export():
            target_path = input_path.text().strip()
            if not target_path:
                QMessageBox.warning(dialog, "Path Error", "Please provide a valid file destination.")
                return

            try:
                if is_attendance:
                    if rb_excel.isChecked():
                        if not target_path.endswith(".xls"): target_path += ".xls"
                        ok = AttendanceExporter.export_to_excel_xml(target_path, data)
                    elif rb_html.isChecked():
                        if not target_path.endswith(".html"): target_path += ".html"
                        ok = AttendanceExporter.export_to_html(target_path, data)
                    else:
                        if not target_path.endswith(".csv"): target_path += ".csv"
                        ok = AttendanceExporter.export_to_csv(target_path, data)
                else:
                    if rb_excel.isChecked():
                        if not target_path.endswith(".xls"): target_path += ".xls"
                        ok = AttendanceExporter.export_audits_to_excel_xml(target_path, data)
                    elif rb_html.isChecked():
                        if not target_path.endswith(".html"): target_path += ".html"
                        ok = AttendanceExporter.export_to_html(target_path, data, title="Security Audits Summary")
                    else:
                        if not target_path.endswith(".csv"): target_path += ".csv"
                        ok = AttendanceExporter.export_audits_to_csv(target_path, data)

                if ok:
                    dialog.accept()
                    # Show Success Dialog with direct action buttons
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Export Successful")
                    msg.setText(f"✓ Report successfully generated ({len(data)} records)!")
                    msg.setInformativeText(f"Saved to:\n{target_path}")
                    msg.setIcon(QMessageBox.Information)
                    msg.setStyleSheet("""
                        QMessageBox { background-color: #161B22; }
                        QLabel { color: #F0F6FC; font-size: 12px; }
                        QPushButton { background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; }
                        QPushButton:hover { background-color: #30363D; }
                    """)
                    
                    btn_open_file = msg.addButton("Open File", QMessageBox.ActionRole)
                    btn_open_dir = msg.addButton("Open Folder", QMessageBox.ActionRole)
                    btn_done = msg.addButton("Done", QMessageBox.AcceptRole)
                    
                    msg.exec()
                    clicked = msg.clickedButton()
                    if clicked == btn_open_file:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(target_path))
                    elif clicked == btn_open_dir:
                        folder = os.path.dirname(target_path)
                        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
                else:
                    QMessageBox.critical(dialog, "Export Failed", "Failed to write report file. Please verify write permissions.")
            except Exception as e:
                logger.error(f"Export execution error: {e}")
                QMessageBox.critical(dialog, "Export Error", f"An error occurred while saving the report:\n{e}")

        btn_do_export.clicked.connect(execute_export)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_do_export)
        d_layout.addLayout(btn_box)

        dialog.exec()

    def clear_action(self):
        if self.active_tab == "attendance":
            self.clear_reports()
        else:
            self.clear_security_audits()

    def clear_security_audits(self):
        """Clear security audit logs."""
        if not self.current_audits_data:
            QMessageBox.information(self, "No Records", "There are no security audit records to clear.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Clear Audits",
            f"Are you sure you want to permanently clear all {len(self.current_audits_data)} security audit logs?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            deleted = self.security_repo.clear_audits()
            QMessageBox.information(self, "Audits Cleared", f"Successfully cleared {deleted} security audit records.")
            self.refresh()

    def clear_reports(self):
        """Clear attendance records with confirmation dialog and filter options."""
        self.refresh()
        if not self.current_report_data:
            QMessageBox.information(self, "No Records", "There are no attendance records to clear.")
            return

        is_filtered = (
            self.dept_filter.currentIndex() > 0 or
            self.year_filter.currentIndex() > 0 or
            bool(self.input_class.text().strip()) or
            bool(self.input_subject.text().strip()) or
            self.active_date_preset != "all"
        )

        if is_filtered:
            count = len(self.current_report_data)
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Clear Attendance Records")
            msg_box.setText(f"Filter is active ({count} matching records found).")
            msg_box.setInformativeText("Choose whether to delete only the filtered records or purge all attendance records permanently:")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStyleSheet("""
                QMessageBox { background-color: #161B22; }
                QLabel { color: #F0F6FC; font-size: 12px; }
                QPushButton { background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #30363D; }
            """)
            
            btn_filtered = msg_box.addButton(f"Clear Filtered ({count})", QMessageBox.ActionRole)
            btn_all = msg_box.addButton("Clear All Records", QMessageBox.DestructiveRole)
            btn_cancel = msg_box.addButton("Cancel", QMessageBox.RejectRole)
            
            msg_box.exec()
            clicked = msg_box.clickedButton()
            
            if clicked == btn_filtered:
                ids = [r["id"] for r in self.current_report_data if "id" in r]
                deleted = self.attendance_repo.delete_records_by_ids(ids)
                QMessageBox.information(self, "Records Cleared", f"Successfully cleared {deleted} filtered attendance record(s).")
                self.refresh()
            elif clicked == btn_all:
                deleted = self.attendance_repo.clear_all_attendance()
                QMessageBox.information(self, "All Records Cleared", f"Successfully cleared all {deleted} attendance record(s) and sessions.")
                self.refresh()
        else:
            total_count = len(self.current_report_data)
            reply = QMessageBox.question(
                self,
                "Confirm Clear All Records",
                f"Are you sure you want to permanently clear all {total_count} attendance record(s)?\n\nThis will permanently delete all session logs. This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                deleted = self.attendance_repo.clear_all_attendance()
                QMessageBox.information(self, "Records Cleared", f"Successfully cleared all {deleted} attendance record(s) and sessions.")
                self.refresh()
