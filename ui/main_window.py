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
from mobile_companion.server import MobileCompanionServer, get_local_ip

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FaceAttend - Local OpenCV SFace Desktop Attendance System")
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

        # 4. Start Mobile Web Companion Server (runs locally in background on Wi-Fi)
        self.mobile_server = MobileCompanionServer(
            self.session_manager, self.attendance_repo, self.student_repo, port=5555
        )
        self.mobile_server.start()

        # 5. Setup UI Shell & Stylesheet
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

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        mobile_url = self.mobile_server.get_url()
        self.status_bar.showMessage(f"FaceAttend Online | Mobile Companion: {mobile_url}")

        # 6. Setup Worker Threads (Camera & Recognition)
        self._init_workers()

        # Check model files availability
        self._verify_models()

        # Load initial dashboard page
        self.switch_page(0)

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #090D16;
            }
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, 'Helvetica Neue', sans-serif;
                color: #F8FAFC;
                font-size: 13px;
            }
            QToolTip {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QStatusBar {
                background-color: #060911;
                color: #94A3B8;
                border-top: 1px solid #1E293B;
                padding: 4px 12px;
                font-size: 12px;
            }
            QScrollBar:vertical {
                background: #090D16;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #1E293B;
                min-height: 24px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
            QScrollBar:horizontal {
                background: #090D16;
                height: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: #1E293B;
                min-width: 24px;
                border-radius: 4px;
            }
        """)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #0B0F19;
                border-right: 1px solid #1E293B;
            }
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                text-align: left;
                padding: 12px 18px;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
                margin: 3px 10px;
            }
            QPushButton:hover {
                background-color: #162032;
                color: #F8FAFC;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                color: #FFFFFF;
                font-weight: 700;
            }
        """)
        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(0, 16, 0, 16)
        self.sidebar_layout.setSpacing(4)

        # Header Row: Logo & Hamburger Collapse Toggle
        self.brand_container = QWidget()
        brand_layout = QVBoxLayout(self.brand_container)
        brand_layout.setContentsMargins(16, 0, 16, 12)
        brand_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        
        brand_icon = QLabel("⚡")
        brand_icon.setStyleSheet("font-size: 20px; background: transparent;")
        
        self.brand_label = QLabel("FaceAttend")
        self.brand_label.setStyleSheet("font-size: 19px; font-weight: 800; color: #FFFFFF; background: transparent; letter-spacing: -0.5px;")
        
        self.btn_toggle_sidebar = QPushButton("☰")
        self.btn_toggle_sidebar.setToolTip("Toggle Compact Sidebar (Mobile Mode)")
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                margin: 0;
            }
            QPushButton:hover {
                background-color: #334155;
                color: white;
            }
        """)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)

        brand_row.addWidget(brand_icon)
        brand_row.addWidget(self.brand_label)
        brand_row.addStretch()
        brand_row.addWidget(self.btn_toggle_sidebar)
        brand_layout.addLayout(brand_row)

        self.brand_badge = QLabel("  LOCAL OPENCV SFACE AI  ")
        self.brand_badge.setStyleSheet("""
            color: #38BDF8;
            background-color: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 6px;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 1px;
            padding: 3px 6px;
        """)
        self.brand_badge.setFixedWidth(160)
        brand_layout.addWidget(self.brand_badge)

        self.sidebar_layout.addWidget(self.brand_container)

        self.nav_buttons = []
        self.nav_items_data = [
            ("📊  Dashboard", "📊", "Dashboard", 0),
            ("📷  Live Attendance", "📷", "Live Attendance", 1),
            ("👤  Register Student", "👤", "Register Student", 2),
            ("👥  Student Directory", "👥", "Student Directory", 3),
            ("📈  Reports & Export", "📈", "Reports & Export", 4),
            ("⚙️  Settings", "⚙️", "Settings", 5)
        ]

        for full_text, short_icon, tooltip, index in self.nav_items_data:
            btn = QPushButton(full_text)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=index: self.switch_page(idx))
            self.sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        self.sidebar_layout.addStretch()

        # Sidebar Bottom: Mobile Web Companion Card
        self.sys_status = QFrame()
        self.sys_status.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 10px;
                margin: 0 10px;
                padding: 10px;
            }
        """)
        sys_layout = QVBoxLayout(self.sys_status)
        sys_layout.setContentsMargins(8, 8, 8, 8)
        sys_layout.setSpacing(3)

        self.status_dot = QLabel("📱 Mobile Web Companion")
        self.status_dot.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        
        mobile_url = f"http://{get_local_ip()}:5555"
        self.status_sub = QLabel(f"<a href='{mobile_url}' style='color: #34D399; text-decoration: none;'>{mobile_url}</a>")
        self.status_sub.setOpenExternalLinks(True)
        self.status_sub.setStyleSheet("font-size: 11px; font-weight: 600; background: transparent; border: none;")

        sys_layout.addWidget(self.status_dot)
        sys_layout.addWidget(self.status_sub)
        self.sidebar_layout.addWidget(self.sys_status)

        return sidebar

    def toggle_sidebar(self):
        self.set_sidebar_collapsed(not self.is_sidebar_collapsed)

    def set_sidebar_collapsed(self, collapsed: bool):
        self.is_sidebar_collapsed = collapsed
        if collapsed:
            self.sidebar_widget.setFixedWidth(68)
            self.brand_label.setVisible(False)
            self.brand_badge.setVisible(False)
            self.sys_status.setVisible(False)
            for idx, btn in enumerate(self.nav_buttons):
                btn.setText(self.nav_items_data[idx][1]) # Short icon only
                btn.setStyleSheet("text-align: center; padding: 12px 0; font-size: 16px; margin: 3px 6px;")
        else:
            self.sidebar_widget.setFixedWidth(250)
            self.brand_label.setVisible(True)
            self.brand_badge.setVisible(True)
            self.sys_status.setVisible(True)
            for idx, btn in enumerate(self.nav_buttons):
                btn.setText(self.nav_items_data[idx][0]) # Full text
                btn.setStyleSheet("text-align: left; padding: 12px 18px; font-size: 13px; margin: 3px 10px;")

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
        for idx, btn in enumerate(self.nav_buttons):
            btn.setChecked(idx == index)

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

    @Slot()
    def apply_saved_settings(self):
        """Apply newly saved settings dynamically."""
        if hasattr(self, "recognition_worker"):
            self.recognition_worker.update_tracker_settings()
        if hasattr(self, "camera_worker"):
            self.camera_worker.update_source(settings.get_capture_source())
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
        if hasattr(self, "mobile_server"):
            self.mobile_server.stop()
        self.camera_worker.stop()
        self.recognition_thread.quit()
        self.recognition_thread.wait(2000)
        event.accept()


