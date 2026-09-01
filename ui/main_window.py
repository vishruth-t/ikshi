import os
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QStatusBar, QMessageBox, QFrame
)

from PySide6.QtCore import Qt, QThread, Slot, Signal
from PySide6.QtGui import QFont, QIcon

from config.settings import settings
from database.connection import DatabaseConnection
from database.repositories import (
    StudentRepository, FaceEmbeddingRepository, SessionRepository, AttendanceRepository
)
from vision.face_detector import FaceDetector
from recognition.sface_model import SFaceRecognizer
from recognition.matcher import FaceMatcher
from enrollment.enrollment_service import EnrollmentService
from attendance.session_manager import SessionManager
from attendance.attendance_service import AttendanceService

from ui.workers.camera_worker import CameraWorker
from ui.workers.recognition_worker import RecognitionWorker
from ui.widgets.camera_view import CameraViewWidget

from ui.pages.dashboard import DashboardPage
from ui.pages.attendance import AttendancePage
from ui.pages.registration import RegistrationPage
from ui.pages.students import StudentsPage
from ui.pages.reports import ReportsPage
from ui.pages.settings import SettingsPage

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ikshi - Local Desktop Attendance System")
        self.resize(1280, 800)

        self.setMinimumSize(480, 480)

        # 1. Initialize Database & Repositories
        self.db = DatabaseConnection(settings.db_path)
        self.student_repo = StudentRepository(self.db)
        self.embedding_repo = FaceEmbeddingRepository(self.db)
        self.session_repo = SessionRepository(self.db)
        self.attendance_repo = AttendanceRepository(self.db)

        # 2. Initialize Core Vision & SFace ML Engines
        self.detector = FaceDetector(settings.detection_model_path)
        self.sface = SFaceRecognizer(settings.recognition_model_path)
        self.matcher = FaceMatcher(self.embedding_repo, self.sface)

        # 3. Initialize Services
        self.enrollment_service = EnrollmentService(self.student_repo, self.embedding_repo, self.detector, self.sface)
        self.session_manager = SessionManager(self.session_repo, self.student_repo, self.attendance_repo)
        self.attendance_service = AttendanceService(self.attendance_repo, self.student_repo, self.session_manager)

        # 4. Setup UI Shell & Stylesheet
        self.is_sidebar_collapsed = False
        self.is_sidebar_collapsed_by_resize = False
        self._setup_style()


        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        self.sidebar_widget = self._create_sidebar()
        main_layout.addWidget(self.sidebar_widget)

        # Shared Camera View Widget
        self.camera_view = CameraViewWidget()

        # Stacked Pages
        self.pages_stack = QStackedWidget()
        
        self.page_dashboard = DashboardPage(self.session_manager, self.student_repo, self.attendance_repo)
        self.page_attendance = AttendancePage(self.camera_view, self.session_manager, self.attendance_repo, self.student_repo)
        self.page_registration = RegistrationPage(self.enrollment_service)
        self.page_students = StudentsPage(self.student_repo)
        self.page_reports = ReportsPage(self.attendance_repo)
        self.page_settings = SettingsPage()

        self.pages_stack.addWidget(self.page_dashboard)
        self.pages_stack.addWidget(self.page_attendance)
        self.pages_stack.addWidget(self.page_registration)
        self.pages_stack.addWidget(self.page_students)
        self.pages_stack.addWidget(self.page_reports)
        self.pages_stack.addWidget(self.page_settings)

        main_layout.addWidget(self.pages_stack, stretch=1)

        # Connect inter-page signals
        self.page_students.request_re_enroll.connect(self.start_re_enrollment)
        self.page_settings.settings_saved.connect(self.apply_saved_settings)
        self.page_attendance.camera_source_changed.connect(self.change_camera_source)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("ikshi Ready | All Systems Operational")



        # 6. Setup Worker Threads (Camera & Recognition)
        self._init_workers()

        # Check model files availability
        self._verify_models()

        # Load initial dashboard page
        self.switch_page(0)

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0D1117;
            }
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #F0F6FC;
                font-size: 13px;
            }
            QToolTip {
                background-color: #161B22;
                color: #F0F6FC;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QStatusBar {
                background-color: #010409;
                color: #8B949E;
                border-top: 1px solid #21262D;
                padding: 4px 12px;
                font-size: 12px;
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
            QScrollBar:horizontal {
                background: #0D1117;
                height: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: #30363D;
                min-width: 24px;
                border-radius: 4px;
            }
        """)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #010409;
                border-right: 1px solid #21262D;
            }
            QPushButton {
                background-color: transparent;
                color: #8B949E;
                text-align: left;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 500;
                border: none;
                border-radius: 6px;
                margin: 2px 10px;
            }
            QPushButton:hover {
                background-color: #161B22;
                color: #F0F6FC;
            }
            QPushButton:checked {
                background-color: #cba6f7;
                color: #11111B;
                font-weight: 700;
            }
        """)
        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(0, 16, 0, 16)
        self.sidebar_layout.setSpacing(2)

        # Header Row: Title & Collapse Toggle
        self.brand_container = QWidget()
        brand_layout = QVBoxLayout(self.brand_container)
        brand_layout.setContentsMargins(16, 0, 16, 16)
        brand_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        
        self.brand_label = QLabel("ikshi")

        self.brand_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #F0F6FC; background: transparent; letter-spacing: -0.2px;")
        
        self.btn_toggle_sidebar = QPushButton("☰")
        self.btn_toggle_sidebar.setToolTip("Toggle Sidebar")
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background-color: #161B22;
                color: #8B949E;
                border: 1px solid #30363D;
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 12px;
                margin: 0;
            }
            QPushButton:hover {
                background-color: #21262D;
                color: #F0F6FC;
            }
        """)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)

        brand_row.addWidget(self.brand_label)
        brand_row.addStretch()
        brand_row.addWidget(self.btn_toggle_sidebar)
        brand_layout.addLayout(brand_row)

        self.brand_badge = QLabel("OpenCV SFace • Local")
        self.brand_badge.setStyleSheet("""
            color: #8B949E;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        brand_layout.addWidget(self.brand_badge)

        self.sidebar_layout.addWidget(self.brand_container)

        self.section_labels = []
        self.nav_buttons = []
        self.nav_items_data = []

        self.nav_sections = [
            ("MAIN", [
                ("Dashboard", "📊", "Dashboard Overview", 0),
                ("Live Attendance", "📷", "Live Attendance", 1),
                ("Student Directory", "👥", "Student Directory", 3),
                ("Reports & Export", "📈", "Reports & Export", 4),
            ]),
            ("MANAGEMENT", [
                ("Register Student", "👤", "Register Student", 2),
            ]),
            ("SYSTEM", [
                ("Settings", "⚙️", "System Settings", 5),
            ])
        ]

        for sec_name, items in self.nav_sections:
            sec_lbl = QLabel(sec_name)
            sec_lbl.setStyleSheet("color: #6E7681; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; padding: 10px 14px 4px 14px; background: transparent; border: none;")
            self.sidebar_layout.addWidget(sec_lbl)
            self.section_labels.append(sec_lbl)

            for full_text, short_icon, tooltip, index in items:
                self.nav_items_data.append((full_text, short_icon, tooltip, index))
                btn = QPushButton(full_text.replace("&", "&&"))
                btn.setToolTip(tooltip)
                btn.setCheckable(True)
                btn.clicked.connect(lambda _, idx=index: self.switch_page(idx))
                self.sidebar_layout.addWidget(btn)
                self.nav_buttons.append(btn)

        self.sidebar_layout.addStretch()
        return sidebar

    def toggle_sidebar(self):
        self.set_sidebar_collapsed(not self.is_sidebar_collapsed)

    def set_sidebar_collapsed(self, collapsed: bool):
        self.is_sidebar_collapsed = collapsed
        if collapsed:
            self.sidebar_widget.setFixedWidth(60)
            self.brand_label.setVisible(False)
            self.brand_badge.setVisible(False)
            for lbl in self.section_labels:
                lbl.setVisible(False)
            for idx, btn in enumerate(self.nav_buttons):
                btn.setText(self.nav_items_data[idx][1]) # Short icon only
                btn.setStyleSheet("text-align: center; padding: 10px 0; font-size: 15px; margin: 2px 6px;")
        else:
            self.sidebar_widget.setFixedWidth(240)
            self.brand_label.setVisible(True)
            self.brand_badge.setVisible(True)
            for lbl in self.section_labels:
                lbl.setVisible(True)
            for idx, btn in enumerate(self.nav_buttons):
                btn.setText(self.nav_items_data[idx][0].replace("&", "&&")) # Full text
                btn.setStyleSheet("text-align: left; padding: 10px 14px; font-size: 13px; margin: 2px 10px;")


    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Responsive reflow: auto-collapse sidebar if window width is narrow (< 850px)
        if self.width() < 850 and not self.is_sidebar_collapsed:
            self.is_sidebar_collapsed_by_resize = True
            self.set_sidebar_collapsed(True)
        elif self.width() >= 950 and self.is_sidebar_collapsed_by_resize and self.is_sidebar_collapsed:
            self.is_sidebar_collapsed_by_resize = False
            self.set_sidebar_collapsed(False)

    def switch_page(self, index: int):
        self.pages_stack.setCurrentIndex(index)
        for idx, (full_text, short_icon, tooltip, page_idx) in enumerate(self.nav_items_data):
            self.nav_buttons[idx].setChecked(page_idx == index)



        # Manage recognition worker state across pages:
        # Pause background recognition during registration (index 2) to avoid concurrent camera processing
        if hasattr(self, "recognition_worker"):
            self.recognition_worker.set_enabled(index != 2)

        # Refresh page data on switch
        current_page = self.pages_stack.widget(index)
        if hasattr(current_page, "refresh"):
            current_page.refresh()

    @Slot(object)
    def start_re_enrollment(self, student):
        """Navigate to registration page pre-loaded with student details for re-enrollment."""
        self.switch_page(2) # Switch to Register Student page
        self.page_registration.load_for_re_enroll(student)
        self.status_bar.showMessage(f"Re-enrolling face samples for {student.name} ({student.student_number})", 6000)

    @Slot(str)
    def change_camera_source(self, new_source: str):
        """Handle quick camera source change from Attendance header."""
        if hasattr(self, "camera_worker"):
            self.camera_worker.update_source(new_source)
        self.status_bar.showMessage(f"Camera source changed to: {new_source}", 4000)

    @Slot()
    def apply_saved_settings(self):
        """Apply newly saved settings dynamically."""
        if hasattr(self, "recognition_worker"):
            self.recognition_worker.update_tracker_settings()
        if hasattr(self, "camera_worker"):
            self.camera_worker.update_source(settings.get_capture_source())
        if hasattr(self, "page_attendance"):
            self.page_attendance.sync_camera_source()
        self.status_bar.showMessage(f"Settings applied. Camera source: {settings.get_capture_source()}", 4000)


    def _init_workers(self):
        # 1. Camera Worker Thread
        self.camera_worker = CameraWorker(settings.get_capture_source())
        self.camera_worker.frame_received.connect(self.camera_view.update_frame)
        self.camera_worker.frame_received.connect(self.page_registration.handle_camera_frame)


        # 2. Recognition Worker Thread
        self.recognition_thread = QThread()
        self.recognition_worker = RecognitionWorker(
            self.detector, self.sface, self.matcher, self.attendance_service
        )
        self.recognition_worker.moveToThread(self.recognition_thread)

        # Connect camera frames to recognition worker
        self.camera_worker.frame_received.connect(self.recognition_worker.process_frame)
        self.recognition_worker.results_ready.connect(self.camera_view.update_recognition_results)
        self.recognition_worker.attendance_event.connect(self.handle_attendance_event)
        self.camera_worker.camera_error.connect(self.handle_camera_error)

        # Start threads
        self.recognition_thread.start()
        self.camera_worker.start()

    @Slot(str, bool)
    def handle_attendance_event(self, message: str, success: bool):
        self.status_bar.showMessage(message, 5000)
        self.page_attendance.refresh()
        self.page_dashboard.refresh()

    @Slot(str)
    def handle_camera_error(self, message: str):
        self.status_bar.showMessage(f"Camera Warning: {message}")

    def _verify_models(self):
        if not self.detector.is_loaded() or not self.sface.is_loaded():
            msg = (
                "Required face-recognition models are missing or failed to load.\n\n"
                "Please run:\n"
                "  python models/download_models.py\n\n"
                f"Detection model: {settings.detection_model_path}\n"
                f"SFace model: {settings.recognition_model_path}"
            )
            QMessageBox.critical(self, "Model Load Error", msg)

    def closeEvent(self, event):
        logger.info("Closing application, stopping background worker threads...")
        self.camera_worker.stop()
        self.recognition_thread.quit()
        self.recognition_thread.wait(2000)
        event.accept()



