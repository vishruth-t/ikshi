import os
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QStatusBar, QMessageBox, QFrame, QApplication,
    QSizePolicy
)

from PySide6.QtCore import Qt, QThread, Slot, Signal, QSize
from PySide6.QtGui import QFont, QIcon
from ui.utils.icons import get_vector_icon
from ui.utils.theme import get_app_stylesheet, get_sidebar_styles, get_palette

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

from ui.pages.attendance import AttendancePage
from ui.pages.registration import RegistrationPage

from ui.pages.students import StudentsPage
from ui.pages.reports import ReportsPage
from ui.pages.settings import SettingsPage

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IKSHI — On-Device Biometric Face Recognition Attendance")
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
        
        self.page_attendance = AttendancePage(self.camera_view, self.session_manager, self.attendance_repo, self.student_repo)
        self.page_students = StudentsPage(self.student_repo)
        self.page_reports = ReportsPage(self.attendance_repo)
        self.page_registration = RegistrationPage(self.enrollment_service)
        self.page_settings = SettingsPage()

        self.pages_stack.addWidget(self.page_attendance)
        self.pages_stack.addWidget(self.page_students)
        self.pages_stack.addWidget(self.page_reports)
        self.pages_stack.addWidget(self.page_registration)
        self.pages_stack.addWidget(self.page_settings)

        main_layout.addWidget(self.pages_stack, stretch=1)

        # Connect inter-page signals
        self.page_students.request_re_enroll.connect(self.start_re_enrollment)
        self.page_students.student_deleted.connect(lambda sid: self.matcher.refresh_cache())
        self.page_registration.enrollment_complete.connect(self.on_enrollment_complete)
        self.page_settings.settings_saved.connect(self.apply_saved_settings)
        self.page_attendance.camera_source_changed.connect(self.change_camera_source)
        self.page_attendance.session_started.connect(self.start_attendance_camera)
        self.page_attendance.session_ended.connect(self.stop_attendance_camera)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("IKSHI Ready | Standby Mode (Cameras Off)")



        # 6. Setup Worker Threads (Camera & Recognition)
        self._init_workers()

        # Check model files availability
        self._verify_models()

        # Load initial dashboard page
        self.switch_page(0)

    def _setup_style(self, theme_name: str = None):
        theme = theme_name or getattr(settings, "theme", "dark")
        self.current_theme = theme
        style = get_app_stylesheet(theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(style)
        self.setStyleSheet(style)

        # Apply sidebar and button styling
        if hasattr(self, "sidebar_widget"):
            sb_qss, exp_btn, col_btn = get_sidebar_styles(theme)
            self.sidebar_widget.setStyleSheet(sb_qss)
            self.expanded_btn_style = exp_btn
            self.collapsed_btn_style = col_btn
            
            p = get_palette(theme)
            if hasattr(self, "brand_label"):
                self.brand_label.setStyleSheet(f"""
                    font-family: 'Space Grotesk', 'Rajdhani', 'Outfit', 'Montserrat', 'Syne', 'Inter', -apple-system, sans-serif;
                    font-size: 20px;
                    font-weight: 900;
                    color: {p['text_primary']};
                    background: transparent;
                    border: none;
                    letter-spacing: 3.5px;
                """)
            if hasattr(self, "btn_toggle_sidebar"):
                self.btn_toggle_sidebar.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {p['bg_card']};
                        border: 1px solid {p['border']};
                        border-radius: 8px;
                        padding: 0;
                    }}
                    QPushButton:hover {{
                        background-color: {p['btn_secondary_hover']};
                        border: 1px solid {p['border_subtle']};
                    }}
                """)
            for idx, btn in enumerate(self.nav_buttons):
                btn.setStyleSheet(self.collapsed_btn_style if self.is_sidebar_collapsed else self.expanded_btn_style)

        # Forward theme to child pages
        if hasattr(self, "page_attendance") and hasattr(self.page_attendance, "apply_theme"):
            self.page_attendance.apply_theme(theme)
        if hasattr(self, "page_students") and hasattr(self.page_students, "apply_theme"):
            self.page_students.apply_theme(theme)
        if hasattr(self, "page_reports") and hasattr(self.page_reports, "apply_theme"):
            self.page_reports.apply_theme(theme)
        if hasattr(self, "page_registration") and hasattr(self.page_registration, "apply_theme"):
            self.page_registration.apply_theme(theme)
        if hasattr(self, "page_settings") and hasattr(self.page_settings, "apply_theme"):
            self.page_settings.apply_theme(theme)

    def _create_sidebar(self) -> QWidget:
        theme = getattr(settings, "theme", "dark")
        p = get_palette(theme)
        sb_qss, exp_btn, col_btn = get_sidebar_styles(theme)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(sb_qss)
        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(0, 16, 0, 16)
        self.sidebar_layout.setSpacing(2)

        # Header Row: Title & Collapse Toggle
        self.brand_container = QWidget()
        self.brand_container.setStyleSheet("background: transparent; border: none;")
        self.brand_layout = QHBoxLayout(self.brand_container)
        self.brand_layout.setContentsMargins(16, 12, 16, 12)
        self.brand_layout.setSpacing(0)
        
        self.brand_label = QLabel("IKSHI")
        self.brand_label.setStyleSheet("""
            font-family: 'Space Grotesk', 'Rajdhani', 'Outfit', 'Montserrat', 'Syne', 'Inter', -apple-system, sans-serif;
            font-size: 20px;
            font-weight: 900;
            color: #FFFFFF;
            background: transparent;
            border: none;
            letter-spacing: 3.5px;
        """)
        
        self.btn_toggle_sidebar = QPushButton()
        self.btn_toggle_sidebar.setIcon(get_vector_icon("sidebar_collapse", size=18))
        self.btn_toggle_sidebar.setIconSize(QSize(18, 18))
        self.btn_toggle_sidebar.setToolTip("Toggle Sidebar (Collapse / Expand)")
        self.btn_toggle_sidebar.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_sidebar.setFixedSize(36, 36)
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #21262D;
                border: 1px solid #8B949E;
            }
        """)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)

        self.brand_spacer = QWidget()
        self.brand_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.brand_layout.addWidget(self.brand_label)
        self.brand_layout.addWidget(self.brand_spacer)
        self.brand_layout.addWidget(self.btn_toggle_sidebar)

        self.sidebar_layout.addWidget(self.brand_container)

        self.section_labels = []
        self.nav_buttons = []
        self.nav_items_data = []

        self.nav_sections = [
            ("MAIN", [
                ("attendance", "Live Attendance", "Live Attendance & Metrics", 0),
                ("students", "Student Directory", "Student Directory & Avatars", 1),
                ("reports", "Reports & Analytics", "Reports, Exports & Security Audits", 2),
            ]),
            ("MANAGEMENT", [
                ("register", "Register Student", "Enroll Student Face Biometrics", 3),
            ]),
            ("SYSTEM", [
                ("settings", "Settings", "Configure Camera, Hardware & Database", 4),
            ]),
        ]

        # Button Stylesheets
        self.expanded_btn_style = """
            QPushButton {
                background-color: transparent;
                color: #8B949E;
                font-weight: 600;
                font-size: 13px;
                text-align: left;
                padding: 10px 14px;
                border: 1px solid transparent;
                border-radius: 8px;
                margin: 2px 10px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #161B22;
                color: #F0F6FC;
                border: 1px solid #30363D;
            }
            QPushButton:checked {
                background-color: #1E1A2E;
                color: #cba6f7;
                font-weight: 700;
                border: 1px solid #cba6f7;
            }
        """

        self.collapsed_btn_style = """
            QPushButton {
                background-color: transparent;
                color: #8B949E;
                border: 1px solid transparent;
                border-radius: 8px;
                margin: 3px 8px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton:hover {
                background-color: #161B22;
                border: 1px solid #30363D;
            }
            QPushButton:checked {
                background-color: #1E1A2E;
                border: 1px solid #cba6f7;
            }
        """

        for sec_name, items in self.nav_sections:
            sec_lbl = QLabel(sec_name)
            sec_lbl.setStyleSheet("color: #6E7681; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; padding: 10px 14px 4px 14px; background: transparent; border: none;")
            self.sidebar_layout.addWidget(sec_lbl)
            self.section_labels.append(sec_lbl)

            for icon_type, label_text, tooltip, index in items:
                icon = get_vector_icon(icon_type)
                self.nav_items_data.append((icon_type, label_text, tooltip, index))
                btn = QPushButton()
                btn.setIcon(icon)
                btn.setIconSize(QSize(18, 18))
                btn.setText(f"  {label_text.replace('&', '&&')}")
                btn.setToolTip(tooltip)
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(self.expanded_btn_style)
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
            self.sidebar_widget.setFixedWidth(64)
            if hasattr(self, "brand_layout"):
                self.brand_layout.setContentsMargins(8, 6, 8, 12)
            self.brand_label.setVisible(False)
            if hasattr(self, "brand_spacer"):
                self.brand_spacer.setVisible(False)
            self.btn_toggle_sidebar.setFixedSize(48, 40)
            self.btn_toggle_sidebar.setIcon(get_vector_icon("sidebar_expand", size=18))
            for lbl in self.section_labels:
                lbl.setVisible(False)
            for idx, btn in enumerate(self.nav_buttons):
                btn.setText("") # No text in collapsed mode - vector icon only
                btn.setIconSize(QSize(20, 20))
                btn.setStyleSheet(self.collapsed_btn_style)
        else:
            self.sidebar_widget.setFixedWidth(240)
            if hasattr(self, "brand_layout"):
                self.brand_layout.setContentsMargins(16, 12, 16, 12)
            self.brand_label.setVisible(True)
            if hasattr(self, "brand_spacer"):
                self.brand_spacer.setVisible(True)
            self.btn_toggle_sidebar.setFixedSize(36, 36)
            self.btn_toggle_sidebar.setIcon(get_vector_icon("sidebar_collapse", size=18))
            for lbl in self.section_labels:
                lbl.setVisible(True)
            for idx, btn in enumerate(self.nav_buttons):
                label_text = self.nav_items_data[idx][1]
                btn.setText(f"  {label_text.replace('&', '&&')}")
                btn.setIconSize(QSize(18, 18))
                btn.setStyleSheet(self.expanded_btn_style)

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
        for idx, (icon_type, label_text, tooltip, page_idx) in enumerate(self.nav_items_data):
            self.nav_buttons[idx].setChecked(page_idx == index)

        # On-demand camera lifecycle across pages:
        if index == 3:  # Register Student page
            if hasattr(self, "camera_worker") and not self.camera_worker.isRunning():
                self.camera_worker.start()
            if hasattr(self, "recognition_worker"):
                self.recognition_worker.set_enabled(False)
        else:  # Attendance (0), Students (1), Reports (2), Settings (4)
            # If no active attendance session, keep cameras turned OFF
            if hasattr(self, "session_manager") and not self.session_manager.is_session_active():
                if hasattr(self, "camera_worker") and self.camera_worker.isRunning():
                    self.camera_worker.stop()
                if hasattr(self, "recognition_worker"):
                    self.recognition_worker.set_enabled(False)
                if hasattr(self, "camera_view"):
                    self.camera_view.show_standby_placeholder()
            else:
                if hasattr(self, "camera_worker") and not self.camera_worker.isRunning():
                    self.camera_worker.start()
                if hasattr(self, "recognition_worker"):
                    self.recognition_worker.set_enabled(True)

        # Refresh page data on switch
        current_page = self.pages_stack.widget(index)
        if hasattr(current_page, "refresh"):
            current_page.refresh()

    @Slot()
    def start_attendance_camera(self):
        """Turn on RGB & IR cameras and start recognition when user starts an attendance session."""
        if hasattr(self, "camera_worker") and not self.camera_worker.isRunning():
            self.camera_worker.start()
        if hasattr(self, "recognition_worker"):
            self.recognition_worker.set_enabled(True)
        self.status_bar.showMessage("Attendance session active | Live camera feeds running", 4000)

    @Slot()
    def stop_attendance_camera(self):
        """Turn off RGB & IR cameras and pause recognition when attendance session ends."""
        if hasattr(self, "camera_worker") and self.camera_worker.isRunning():
            self.camera_worker.stop()
        if hasattr(self, "recognition_worker"):
            self.recognition_worker.set_enabled(False)
        if hasattr(self, "camera_view"):
            self.camera_view.show_standby_placeholder()
        self.status_bar.showMessage("Attendance session ended | Cameras turned off (Standby)", 4000)

    @Slot(object)
    def start_re_enrollment(self, student):
        """Navigate to registration page pre-loaded with student details for re-enrollment."""
        self.switch_page(3) # Switch to Register Student page
        self.page_registration.load_for_re_enroll(student)
        self.status_bar.showMessage(f"Re-enrolling face samples for {student.name} ({student.student_number})", 6000)

    @Slot(str)
    def change_camera_source(self, new_source: str):
        """Handle quick camera source change from Attendance header."""
        if hasattr(self, "camera_worker"):
            self.camera_worker.camera_source = self.camera_worker._parse_source(new_source)
            if self.session_manager.is_session_active() or self.pages_stack.currentIndex() == 3:
                self.camera_worker.update_source(new_source)
        self.status_bar.showMessage(f"Camera source changed to: {new_source}", 4000)

    @Slot()
    def apply_saved_settings(self):
        """Apply newly saved settings dynamically."""
        # 1. Update theme
        self._setup_style(getattr(settings, "theme", "dark"))

        if hasattr(self, "recognition_worker"):
            self.recognition_worker.update_tracker_settings()
        if hasattr(self, "camera_worker"):
            if self.session_manager.is_session_active() or self.pages_stack.currentIndex() == 3:
                self.camera_worker.update_source(
                    settings.get_capture_source(),
                    settings.get_ir_capture_source(),
                    settings.enable_ir_liveness
                )
            else:
                self.camera_worker.camera_source = self.camera_worker._parse_source(settings.get_capture_source())
                self.camera_worker.ir_source = settings.get_ir_capture_source()
                self.camera_worker.enable_ir = settings.enable_ir_liveness
        if hasattr(self, "page_attendance"):
            self.page_attendance.sync_camera_source()
        self.status_bar.showMessage(f"Settings applied. Theme: {settings.theme.capitalize()} | Camera: {settings.get_capture_source()} | IR: {'Enabled' if settings.enable_ir_liveness else 'Disabled'}", 4000)

    def _init_workers(self):
        # 1. Camera Worker Thread (kept off in Standby by default)
        self.camera_worker = CameraWorker(settings.get_capture_source())
        self.camera_worker.frame_received.connect(self.camera_view.update_frame)
        self.camera_worker.frames_captured.connect(self.page_registration.handle_frames_captured)

        # 2. Recognition Worker Thread
        self.recognition_thread = QThread()
        self.recognition_worker = RecognitionWorker(
            self.detector, self.sface, self.matcher, self.attendance_service
        )
        self.recognition_worker.set_enabled(False) # Paused in Standby
        self.recognition_worker.moveToThread(self.recognition_thread)

        # Connect dual camera frames to recognition worker
        self.camera_worker.frames_captured.connect(self.recognition_worker.process_frames)
        self.recognition_worker.results_ready.connect(self.camera_view.update_recognition_results)
        self.recognition_worker.attendance_event.connect(self.handle_attendance_event)
        self.camera_worker.camera_error.connect(self.handle_camera_error)
        self.camera_worker.ir_status_changed.connect(self.handle_ir_status)

        # Start recognition event loop thread (camera worker starts on session activation)
        self.recognition_thread.start()
    @Slot(bool, str)
    def handle_ir_status(self, active: bool, message: str):
        if hasattr(self, "page_attendance"):
            self.page_attendance.update_ir_status(active, message)
        if hasattr(self, "page_registration"):
            self.page_registration.update_ir_status(active, message)
        if active:
            self.status_bar.showMessage(f"✓ {message}", 4000)
        elif settings.enable_ir_liveness:
            self.status_bar.showMessage(f"⚠ {message}", 5000)

    @Slot(str, bool)
    def handle_attendance_event(self, message: str, success: bool):
        self.status_bar.showMessage(message, 5000)
        self.page_attendance.refresh()
        if success and getattr(settings, "enable_sound_chime", True):
            from ui.utils.sound_effects import SoundManager
            SoundManager.get_instance().play_verified_chime()

    @Slot()
    def on_enrollment_complete(self):
        self.matcher.refresh_cache()
        self.page_students.refresh()
        self.status_bar.showMessage("✓ Student Enrolled Successfully | Biometric Embeddings Cached", 5000)

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
        try:
            if hasattr(self, 'camera_worker'):
                self.camera_worker.stop()
            if hasattr(self, 'recognition_thread') and self.recognition_thread.isRunning():
                self.recognition_thread.quit()
                self.recognition_thread.wait(1000)
        except Exception as e:
            logger.warning(f"Error during thread shutdown: {e}")
        event.accept()



