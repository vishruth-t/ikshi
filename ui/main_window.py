import os
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QStatusBar, QMessageBox
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
        self.setWindowTitle("FaceAttend - Local OpenCV SFace Desktop Attendance System")
        self.resize(1280, 800)

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
        self._setup_style()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

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

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("FaceAttend System Initialized.")

        # 5. Setup Worker Threads (Camera & Recognition)
        self._init_workers()

        # Check model files availability
        self._verify_models()

        # Load initial dashboard page
        self.switch_page(0)

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F172A;
            }
            QWidget {
                font-family: 'Segoe UI', Inter, sans-serif;
                color: #F8FAFC;
            }
            QStatusBar {
                background-color: #0B0F19;
                color: #94A3B8;
            }
        """)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #0B0F19;
                border-right: 1px solid #1E293B;
            }
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                text-align: left;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                margin: 4px 8px;
            }
            QPushButton:hover {
                background-color: #1E293B;
                color: #F8FAFC;
            }
            QPushButton:checked {
                background-color: #2563EB;
                color: #FFFFFF;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(5)

        # App Brand Title
        brand_label = QLabel("  FaceAttend")
        brand_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #60A5FA; padding-bottom: 20px;")
        layout.addWidget(brand_label)

        self.nav_buttons = []
        nav_items = [
            ("📊 Dashboard", 0),
            ("📷 Live Attendance", 1),
            ("👤 Register Student", 2),
            ("👥 Student Directory", 3),
            ("📈 Reports & Export", 4),
            ("⚙️ Settings", 5)
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=index: self.switch_page(idx))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()
        return sidebar

    def switch_page(self, index: int):
        self.pages_stack.setCurrentIndex(index)
        for idx, btn in enumerate(self.nav_buttons):
            btn.setChecked(idx == index)

        # Refresh page data on switch
        current_page = self.pages_stack.widget(index)
        if hasattr(current_page, "refresh"):
            current_page.refresh()

    def _init_workers(self):
        # 1. Camera Worker Thread
        self.camera_worker = CameraWorker(settings.camera_index)
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
