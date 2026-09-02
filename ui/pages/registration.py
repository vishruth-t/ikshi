import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QStackedWidget, QFormLayout, QProgressBar, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, Signal
from ui.widgets.camera_view import CameraViewWidget
from enrollment.enrollment_service import EnrollmentService
from database.models import Student, RecognitionResult
from vision.image_utils import validate_face_sample
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS
from config.settings import settings

REGISTRATION_POSES = [
    {
        "id": 0,
        "badge": "1. Frontal",
        "title": "Pose 1/5: Center & Look Straight Ahead",
        "instruction": "Look directly at the camera with a neutral, forward-facing expression.",
        "target": "center",
        "action_text": "Frontal (Center)"
    },
    {
        "id": 1,
        "badge": "2. Turn Left",
        "title": "Pose 2/5: Turn Head Slightly Left (~20°)",
        "instruction": "Turn your head slightly to your left so the camera captures your left facial profile.",
        "target": "left",
        "action_text": "Left Profile (~20°)"
    },
    {
        "id": 2,
        "badge": "3. Turn Right",
        "title": "Pose 3/5: Turn Head Slightly Right (~20°)",
        "instruction": "Turn your head slightly to your right so the camera captures your right facial profile.",
        "target": "right",
        "action_text": "Right Profile (~20°)"
    },
    {
        "id": 3,
        "badge": "4. Chin Up",
        "title": "Pose 4/5: Tilt Head Slightly Upward (~15°)",
        "instruction": "Slightly raise your chin to capture lower jawline and eye-ridge angles.",
        "target": "up",
        "action_text": "Upward Tilt (~15°)"
    },
    {
        "id": 4,
        "badge": "5. Smile / Down",
        "title": "Pose 5/5: Natural Expression / Slight Smile",
        "instruction": "Look forward with a natural smile or slight head tilt down to capture expressive variation.",
        "target": "smile_down",
        "action_text": "Smile / Down"
    }
]


def estimate_face_pose(landmarks: np.ndarray) -> tuple:
    """
    Estimate head pose (yaw_ratio, pitch_ratio, description) from 5 facial keypoints.
    yaw_ratio > 0.08: Facing Left (user perspective)
    yaw_ratio < -0.08: Facing Right (user perspective)
    pitch_ratio < 0.44: Tilting Upward
    pitch_ratio > 0.62: Tilting Downward
    """
    if landmarks is None or len(landmarks) < 5:
        return 0.0, 0.5, "Frontal"

    re_x, re_y = landmarks[0]
    le_x, le_y = landmarks[1]
    n_x, n_y = landmarks[2]
    rm_x, rm_y = landmarks[3]
    lm_x, lm_y = landmarks[4]

    d_l = abs(n_x - re_x)
    d_r = abs(le_x - n_x)
    yaw = (d_l - d_r) / max(1e-5, (d_l + d_r))

    eye_y = (re_y + le_y) / 2.0
    mouth_y = (rm_y + lm_y) / 2.0
    pitch = (n_y - eye_y) / max(1e-5, (mouth_y - eye_y))

    if yaw > 0.10:
        desc = "Facing Left"
    elif yaw < -0.10:
        desc = "Facing Right"
    elif pitch < 0.44:
        desc = "Tilted Up"
    elif pitch > 0.62:
        desc = "Tilted Down"
    else:
        desc = "Frontal Center"

    return yaw, pitch, desc


class RegistrationPage(QWidget):
    enrollment_complete = Signal()

    def __init__(self, enrollment_service: EnrollmentService, parent=None):
        super().__init__(parent)
        self.enrollment_service = enrollment_service
        self.camera_view = CameraViewWidget(self)
        self.captured_rgb_features = []
        self.captured_ir_features = []
        self.capture_stage = "rgb"  # "rgb" or "ir"
        self.current_rgb_frame = None
        self.current_ir_frame = None
        self.current_frame = None
        self.re_enroll_student_id = None
        self.current_pose_idx = 0
        self.pose_pills = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        self.title_label = QLabel("Register Student")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #F0F6FC; letter-spacing: -0.2px;")
        header_row.addWidget(self.title_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Horizontal Stepper Indicator
        self.stepper_container = QFrame()
        self.stepper_container.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 4px 12px;
            }
        """)
        stepper_layout = QHBoxLayout(self.stepper_container)
        stepper_layout.setContentsMargins(8, 4, 8, 4)

        self.step_label_1 = QLabel("1. Student Details")
        self.step_label_2 = QLabel("2. Face Capture (5 Multi-Angle Samples)")
        self.step_label_3 = QLabel("3. Complete")

        self.step_labels = [self.step_label_1, self.step_label_2, self.step_label_3]
        for i, lbl in enumerate(self.step_labels):
            stepper_layout.addWidget(lbl)
            if i < 2:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #484F58; font-weight: 600;")
                stepper_layout.addWidget(arrow)

        layout.addWidget(self.stepper_container)

        # Wizard Step Stack
        self.wizard_stack = QStackedWidget()
        layout.addWidget(self.wizard_stack)

        # Build Wizard Steps
        self._init_step1_info()
        self._init_step2_capture()
        self._init_step3_complete()

        self._update_stepper_ui(0)
        self.wizard_stack.setCurrentIndex(0)

    def apply_theme(self, theme_name: str = None):
        from ui.utils.theme import get_palette
        theme = theme_name or getattr(settings, "theme", "dark")
        p = get_palette(theme)

        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {p['text_primary']}; letter-spacing: -0.2px; background: transparent; border: none;")
        self.stepper_container.setStyleSheet(f"background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 6px; padding: 4px 12px;")
        if hasattr(self, "step1_card"):
            self.step1_card.setStyleSheet(f"background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 8px; padding: 18px;")
        if hasattr(self, "guide_card"):
            self.guide_card.setStyleSheet(f"background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 6px; padding: 10px 14px;")
        if hasattr(self, "pose_ribbon"):
            self.pose_ribbon.setStyleSheet(f"background-color: {p['bg_card_inner']}; border: 1px solid {p['border']}; border-radius: 6px; padding: 4px;")
        self._update_stepper_ui(self.wizard_stack.currentIndex())

    def update_ir_status(self, active: bool, message: str = ""):
        self.is_ir_hardware_active = active
        if hasattr(self, "sensor_mode_badge"):
            if active:
                self.sensor_mode_badge.setText("● Dual-Sensor Active (RGB + IR Camera)")
                self.sensor_mode_badge.setStyleSheet("color: #3FB950; font-size: 11px; font-weight: 600; background: #162B1D; border: 1px solid #238636; border-radius: 4px; padding: 3px 8px;")
            elif settings.enable_ir_liveness:
                self.sensor_mode_badge.setText("📷 Standard Webcam Mode (5 Angles • IR Not Found)")
                self.sensor_mode_badge.setStyleSheet("color: #D29922; font-size: 11px; font-weight: 600; background: #282114; border: 1px solid #9E6A03; border-radius: 4px; padding: 3px 8px;")
            else:
                self.sensor_mode_badge.setText("📷 Standard Webcam Mode (5 Angles)")
                self.sensor_mode_badge.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: 600; background: #21262D; border: 1px solid #30363D; border-radius: 4px; padding: 3px 8px;")
        self._update_stepper_ui(self.wizard_stack.currentIndex())

    def _update_stepper_ui(self, current_step: int):
        has_ir = settings.enable_ir_liveness and (
            getattr(self, "is_ir_hardware_active", False) or 
            (self.current_ir_frame is not None and getattr(self.current_ir_frame, "size", 0) > 0)
        )
        self.step_label_2.setText("2. Face Capture (5 RGB + 5 IR Angles)" if has_ir else "2. Face Capture (5 Multi-Angle Samples)")
        for idx, lbl in enumerate(self.step_labels):
            if idx == current_step:
                lbl.setStyleSheet("""
                    color: #cba6f7;
                    font-weight: 600;
                    font-size: 12px;
                    background-color: #21262D;
                    border: 1px solid #30363D;
                    border-radius: 4px;
                    padding: 3px 8px;
                """)
            elif idx < current_step:
                lbl.setStyleSheet("color: #3FB950; font-weight: 600; font-size: 12px; padding: 3px 6px;")
            else:
                lbl.setStyleSheet("color: #6E7681; font-weight: 500; font-size: 12px; padding: 3px 6px;")

    def load_for_re_enroll(self, student: Student):
        """Pre-populate wizard for re-enrolling an existing student's face samples."""
        self._reset_wizard()
        self.re_enroll_student_id = student.id
        self.title_label.setText(f"Re-Enroll Face Samples — {student.name}")
        self.input_num.setText(student.student_number)
        self.input_num.setEnabled(False)
        self.input_name.setText(student.name)
        if student.department in DEFAULT_DEPARTMENTS:
            self.input_dept.setCurrentText(student.department)
        if student.year in DEFAULT_ACADEMIC_YEARS:
            self.input_year.setCurrentText(student.year)
        self._goto_step2()

    @Slot(np.ndarray, object)
    def handle_frames_captured(self, frame_rgb: np.ndarray, frame_ir: object = None):
        """Handles synchronized dual camera frames with multi-angle pose feedback."""
        self.current_rgb_frame = frame_rgb
        self.current_ir_frame = frame_ir if isinstance(frame_ir, np.ndarray) else None
        self.current_frame = frame_rgb

        # Only process & render video feed if user is on Step 2 (Capture step)
        if self.wizard_stack.currentIndex() != 1:
            return

        is_ir_stage = (self.capture_stage == "ir")
        if is_ir_stage and self.current_ir_frame is not None:
            ir_raw = self.current_ir_frame
            if len(ir_raw.shape) == 2:
                active_frame = cv2.cvtColor(ir_raw, cv2.COLOR_GRAY2BGR)
            elif len(ir_raw.shape) == 3 and ir_raw.shape[2] == 1:
                active_frame = cv2.cvtColor(ir_raw, cv2.COLOR_GRAY2BGR)
            else:
                active_frame = ir_raw.copy()
            stage_prefix = "IR Sensor"
        else:
            active_frame = frame_rgb.copy() if frame_rgb is not None else None
            stage_prefix = "RGB Camera"

        if active_frame is None:
            return

        cur_pose = REGISTRATION_POSES[min(self.current_pose_idx, 4)]

        if self.enrollment_service.detector and self.enrollment_service.detector.is_loaded():
            faces = self.enrollment_service.detector.detect(active_frame)
            is_valid, title, subtitle = validate_face_sample(active_frame, faces[0].bbox if faces else (0,0,0,0), len(faces))
            
            if is_valid and faces:
                # Real-time multi-angle pose alignment check
                yaw, pitch, pose_desc = estimate_face_pose(faces[0].landmarks)
                target = cur_pose["target"]
                
                angle_matched = False
                if target == "center":
                    angle_matched = (abs(yaw) <= 0.18 and 0.36 <= pitch <= 0.65)
                elif target == "left":
                    angle_matched = (yaw > 0.08)
                elif target == "right":
                    angle_matched = (yaw < -0.08)
                elif target == "up":
                    angle_matched = (pitch < 0.46)
                elif target == "smile_down":
                    angle_matched = (pitch >= 0.44 or abs(yaw) <= 0.25)

                if angle_matched:
                    self.prompt_title_label.setText(f"✓ {cur_pose['title']} — Angle Verified!")
                    self.prompt_title_label.setStyleSheet("color: #3FB950; font-weight: 700; font-size: 13px; border: none; background: transparent;")
                    self.prompt_sub_label.setText(f"Great angle detected ({pose_desc}). Click capture to record sample.")
                else:
                    self.prompt_title_label.setText(f"👉 {cur_pose['title']} (Current: {pose_desc})")
                    self.prompt_title_label.setStyleSheet("color: #E3B341; font-weight: 700; font-size: 13px; border: none; background: transparent;")
                    self.prompt_sub_label.setText(cur_pose["instruction"])

                self.btn_capture.setEnabled(True)
                self.btn_capture.setText(f"📸 Capture Pose {self.current_pose_idx + 1}: {cur_pose['action_text']}")
            else:
                self.prompt_title_label.setText(f"{stage_prefix}: {title}")
                self.prompt_sub_label.setText(subtitle)
                self.prompt_title_label.setStyleSheet("color: #E3B341; font-weight: 700; font-size: 13px; border: none; background: transparent;")
                self.btn_capture.setText(f"📸 Capture Pose {self.current_pose_idx + 1}: {cur_pose['action_text']}")

            results = []
            for face in faces:
                res = RecognitionResult(
                    name=title if not is_valid else f"{stage_prefix} • {cur_pose['badge']}",
                    similarity=face.score,
                    bbox=face.bbox,
                    confirmed=is_valid
                )
                results.append(res)
            self.camera_view.update_recognition_results(results)

        self.camera_view.update_frame(active_frame)

    @Slot(np.ndarray)
    def handle_camera_frame(self, frame: np.ndarray):
        """Single-frame slot for RGB only backward compatibility."""
        self.handle_frames_captured(frame, None)

    def _init_step1_info(self):
        step1 = QWidget()
        l = QVBoxLayout(step1)
        l.setContentsMargins(0, 8, 0, 0)
        l.setSpacing(14)

        self.step1_card = QFrame()
        self.step1_card.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 18px;
            }
        """)
        card_layout = QVBoxLayout(self.step1_card)
        card_layout.setSpacing(14)

        desc = QLabel("Enter the student's biographical and academic details to begin registration.")
        desc.setStyleSheet("color: #8B949E; font-size: 13px; border: none; background: transparent;")
        card_layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(12)

        self.input_num = QLineEdit()
        self.input_num.setPlaceholderText("e.g. STU-2026-001")

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Darshan Sharma")

        # Department Dropdown
        self.input_dept = QComboBox()
        self.input_dept.addItems(DEFAULT_DEPARTMENTS)
        self.input_dept.setCurrentText(settings.default_department if settings.default_department in DEFAULT_DEPARTMENTS else DEFAULT_DEPARTMENTS[0])

        # Academic Year Dropdown
        self.input_year = QComboBox()
        self.input_year.addItems(DEFAULT_ACADEMIC_YEARS)
        self.input_year.setCurrentText(settings.default_academic_year if settings.default_academic_year in DEFAULT_ACADEMIC_YEARS else DEFAULT_ACADEMIC_YEARS[0])

        def make_form_lbl(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #8B949E; font-weight: 500; font-size: 12px; border: none; background: transparent;")
            return lbl

        form.addRow(make_form_lbl("Student ID:"), self.input_num)
        form.addRow(make_form_lbl("Full Name:"), self.input_name)
        form.addRow(make_form_lbl("Department:"), self.input_dept)
        form.addRow(make_form_lbl("Academic Year:"), self.input_year)
        card_layout.addLayout(form)

        btn_next = QPushButton("Proceed to Face Capture →")
        btn_next.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7;
                color: #11111B;
                font-weight: 700;
                font-size: 13px;
                padding: 9px 18px;
                border-radius: 6px;
                border: 1px solid #cba6f7;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        btn_next.clicked.connect(self._goto_step2)
        card_layout.addWidget(btn_next, alignment=Qt.AlignRight)


        l.addWidget(self.step1_card)
        l.addStretch()
        self.wizard_stack.addWidget(step1)

    def _init_step2_capture(self):
        step2 = QWidget()
        l = QVBoxLayout(step2)
        l.setContentsMargins(0, 8, 0, 0)
        l.setSpacing(10)

        # Multi-Angle Guided Pose Ribbon (5 Target Angles)
        self.pose_ribbon = QFrame()
        self.pose_ribbon.setStyleSheet("background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px; padding: 4px;")
        ribbon_layout = QHBoxLayout(self.pose_ribbon)
        ribbon_layout.setContentsMargins(4, 2, 4, 2)
        ribbon_layout.setSpacing(6)
        
        self.pose_pills = []
        for p in REGISTRATION_POSES:
            pill = QLabel(p["badge"])
            pill.setAlignment(Qt.AlignCenter)
            pill.setStyleSheet("background-color: #161B22; color: #6E7681; border: 1px solid #30363D; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 500;")
            ribbon_layout.addWidget(pill, stretch=1)
            self.pose_pills.append(pill)
        l.addWidget(self.pose_ribbon)

        # Dynamic Actionable Guidance Card
        self.guide_card = QFrame()
        self.guide_card.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 10px 14px;
            }
        """)
        g_layout = QVBoxLayout(self.guide_card)
        g_layout.setContentsMargins(8, 6, 8, 6)
        g_layout.setSpacing(2)

        header_line = QHBoxLayout()
        self.prompt_title_label = QLabel("Pose 1/5: Center & Look Straight Ahead")
        self.prompt_title_label.setStyleSheet("color: #E3B341; font-weight: 700; font-size: 13px; border: none; background: transparent;")
        
        self.sensor_mode_badge = QLabel("📷 Standard Webcam Mode (5 Angles)")
        self.sensor_mode_badge.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: 600; background: #21262D; border: 1px solid #30363D; border-radius: 4px; padding: 3px 8px;")

        self.samples_counter_badge = QLabel("0 / 5 Samples")
        self.samples_counter_badge.setStyleSheet("""
            background-color: #21262D;
            color: #cba6f7;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_line.addWidget(self.prompt_title_label)
        header_line.addStretch()
        header_line.addWidget(self.sensor_mode_badge)
        header_line.addWidget(self.samples_counter_badge)
        g_layout.addLayout(header_line)

        self.prompt_sub_label = QLabel("Look directly at the camera with a neutral, forward-facing expression.")
        self.prompt_sub_label.setStyleSheet("color: #8B949E; font-size: 12px; border: none; background: transparent;")
        g_layout.addWidget(self.prompt_sub_label)

        l.addWidget(self.guide_card)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 2px;
                background-color: #21262D;
            }
            QProgressBar::chunk {
                background-color: #238636;
                border-radius: 2px;
            }
        """)
        l.addWidget(self.progress_bar)

        # Camera View
        l.addWidget(self.camera_view, stretch=1)

        # Action Buttons Row
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("← Back to Details")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #C9D1D9;
                border: 1px solid #30363D;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363D;
                color: white;
            }
        """)
        btn_cancel.clicked.connect(lambda: [self._update_stepper_ui(0), self.wizard_stack.setCurrentIndex(0)])

        self.btn_capture = QPushButton("📸 Capture Pose 1: Frontal (Center)")
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 9px 20px;
                border-radius: 6px;
                border: 1px solid #2EA043;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
            QPushButton:disabled {
                background-color: #21262D;
                color: #484F58;
                border: 1px solid #30363D;
            }
        """)
        self.btn_capture.clicked.connect(self._capture_sample)

        btn_box.addWidget(btn_cancel)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_capture)
        l.addLayout(btn_box)

        self.wizard_stack.addWidget(step2)

    def _update_pose_pills(self):
        """Refreshes visual style of the 5 pose pills based on current enrollment progress."""
        for i, pill in enumerate(self.pose_pills):
            p = REGISTRATION_POSES[i]
            if i < self.current_pose_idx:
                pill.setStyleSheet("background-color: #13231B; color: #3FB950; border: 1px solid #238636; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 600;")
                pill.setText(f"✓ {p['badge']}")
            elif i == self.current_pose_idx:
                pill.setStyleSheet("background-color: #1E1A2E; color: #cba6f7; border: 1px solid #cba6f7; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 700;")
                pill.setText(f"● {p['badge']}")
            else:
                pill.setStyleSheet("background-color: #161B22; color: #6E7681; border: 1px solid #30363D; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 500;")
                pill.setText(p["badge"])

    def _init_step3_complete(self):
        step3 = QWidget()
        l = QVBoxLayout(step3)
        l.setContentsMargins(0, 16, 0, 0)
        l.setSpacing(16)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(32, 28, 32, 28)
        c_layout.setSpacing(16)

        self.summary_label = QLabel("Registration Complete")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #3FB950; background: transparent; border: none;")
        c_layout.addWidget(self.summary_label)

        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("font-size: 13px; color: #8B949E; background: transparent; border: none; padding: 4px 12px;")
        self.details_label.setWordWrap(True)
        self.details_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        c_layout.addWidget(self.details_label)

        btn_box = QHBoxLayout()
        btn_box.setAlignment(Qt.AlignCenter)
        btn_finish = QPushButton("Register Another Student")
        btn_finish.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7;
                color: #11111B;
                font-weight: 700;
                font-size: 13px;
                padding: 10px 24px;
                border-radius: 6px;
                border: 1px solid #cba6f7;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        btn_finish.clicked.connect(self._reset_wizard)
        btn_box.addWidget(btn_finish)
        c_layout.addLayout(btn_box)

        l.addWidget(card)
        l.addStretch()
        self.wizard_stack.addWidget(step3)

    def _goto_step2(self):
        num = self.input_num.text().strip()
        name = self.input_name.text().strip()
        dept = self.input_dept.currentText().strip()
        year = self.input_year.currentText().strip()
        
        if not num:
            QMessageBox.warning(self, "Validation Error", "Please provide a valid Student ID / Roll Number.")
            return
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please provide the student's Full Name.")
            return
        if not dept:
            QMessageBox.warning(self, "Validation Error", "Please select a Department.")
            return
        if not year:
            QMessageBox.warning(self, "Validation Error", "Please select an Academic Year.")
            return

        self.captured_rgb_features.clear()
        self.captured_ir_features.clear()
        self.capture_stage = "rgb"
        self.current_pose_idx = 0

        has_ir = settings.enable_ir_liveness and (
            getattr(self, "is_ir_hardware_active", False) or 
            (self.current_ir_frame is not None and getattr(self.current_ir_frame, "size", 0) > 0)
        )
        total_samples = 10 if has_ir else 5
        self.progress_bar.setRange(0, total_samples)
        self.progress_bar.setValue(0)
        
        if has_ir:
            self.sensor_mode_badge.setText("● Dual-Sensor Mode (RGB + IR Active)")
            self.sensor_mode_badge.setStyleSheet("color: #3FB950; font-size: 11px; font-weight: 600; background: #162B1D; border: 1px solid #238636; border-radius: 4px; padding: 3px 8px;")
            self.samples_counter_badge.setText("Stage 1/2: RGB Face (0 / 5 Angles)")
        else:
            self.sensor_mode_badge.setText("📷 Standard Webcam Mode (5 Angles • No IR Sensor)")
            self.sensor_mode_badge.setStyleSheet("color: #D29922; font-size: 11px; font-weight: 600; background: #282114; border: 1px solid #9E6A03; border-radius: 4px; padding: 3px 8px;")
            self.samples_counter_badge.setText("0 / 5 Multi-Angle Samples")
        
        first_pose = REGISTRATION_POSES[0]
        self.prompt_title_label.setText(first_pose["title"])
        self.prompt_sub_label.setText(first_pose["instruction"])
        self.btn_capture.setText(f"📸 Capture Pose 1: {first_pose['action_text']}")
        self._update_pose_pills()
        self._update_stepper_ui(1)
        self.wizard_stack.setCurrentIndex(1)

    def _capture_sample(self):
        has_ir = settings.enable_ir_liveness and (
            getattr(self, "is_ir_hardware_active", False) or 
            (self.current_ir_frame is not None and getattr(self.current_ir_frame, "size", 0) > 0)
        )
        
        if self.capture_stage == "rgb":
            frame_to_use = self.current_rgb_frame
            is_ir = False
        else:
            frame_to_use = self.current_ir_frame
            is_ir = True

        if frame_to_use is None:
            self.prompt_title_label.setText("No camera frame available")
            self.prompt_sub_label.setText("Please check that your camera device is connected.")
            return

        success, msg, feature = self.enrollment_service.process_sample(frame_to_use, is_ir=is_ir)
        if not success:
            self.prompt_title_label.setText("Capture failed")
            self.prompt_sub_label.setText(msg)
            return

        if success and feature is not None:
            try:
                from ui.utils.sound_effects import SoundManager
                SoundManager.get_instance().play_verified_chime()
            except Exception:
                pass

            if self.capture_stage == "rgb":
                if len(self.captured_rgb_features) == 0:
                    self.first_rgb_capture_frame = frame_to_use.copy()
                self.captured_rgb_features.append(feature)
                self.current_pose_idx += 1
                rgb_count = len(self.captured_rgb_features)
                self.progress_bar.setValue(rgb_count)
                
                badge_str = f"Stage 1/2: RGB Face ({rgb_count} / 5 Angles)" if has_ir else f"{rgb_count} / 5 Multi-Angle Samples"
                self.samples_counter_badge.setText(badge_str)
                self._update_pose_pills()

                if rgb_count < 5:
                    next_pose = REGISTRATION_POSES[self.current_pose_idx]
                    self.prompt_title_label.setText(f"✓ Recorded! Next: {next_pose['title']}")
                    self.prompt_title_label.setStyleSheet("color: #3FB950; font-weight: 700; font-size: 13px; border: none; background: transparent;")
                    self.prompt_sub_label.setText(next_pose["instruction"])
                    self.btn_capture.setText(f"📸 Capture Pose {self.current_pose_idx + 1}: {next_pose['action_text']}")
                else:
                    if has_ir:
                        # Advance to Stage 2 (IR Camera capture)
                        self.capture_stage = "ir"
                        self.current_pose_idx = 0
                        self.samples_counter_badge.setText("Stage 2/2: IR Sensor (0 / 5 Angles)")
                        self.prompt_title_label.setText("Stage 2/2: Infrared (IR) Anti-Spoofing Capture")
                        self.prompt_title_label.setStyleSheet("color: #cba6f7; font-weight: 700; font-size: 13px; border: none; background: transparent;")
                        self.prompt_sub_label.setText("RGB samples completed! Now position face in front of the IR sensor for anti-spoofing enrollment.")
                        self._update_pose_pills()
                    else:
                        # Single-camera laptop fallback: directly finalize with 5 multi-angle RGB photos
                        self._finalize_registration()
            else:
                self.captured_ir_features.append(feature)
                self.current_pose_idx += 1
                ir_count = len(self.captured_ir_features)
                self.progress_bar.setValue(5 + ir_count)
                self.samples_counter_badge.setText(f"Stage 2/2: IR Sensor ({ir_count} / 5 Angles)")
                self._update_pose_pills()

                if ir_count < 5:
                    next_pose = REGISTRATION_POSES[min(self.current_pose_idx, 4)]
                    self.prompt_title_label.setText(f"✓ IR Recorded! Next: {next_pose['title']}")
                    self.prompt_title_label.setStyleSheet("color: #3FB950; font-weight: 700; font-size: 13px; border: none; background: transparent;")
                    self.prompt_sub_label.setText(next_pose["instruction"])
                    self.btn_capture.setText(f"📸 Capture Pose {self.current_pose_idx + 1}: {next_pose['action_text']}")
                else:
                    self._finalize_registration()

    def _finalize_registration(self):
        student_name = self.input_name.text().strip()
        student_number = self.input_num.text().strip()
        department = self.input_dept.currentText().strip()
        academic_year = self.input_year.currentText().strip()

        rgb_count = len(self.captured_rgb_features)
        ir_count = len(self.captured_ir_features)

        pose_tags = [p["target"] for p in REGISTRATION_POSES]

        if self.re_enroll_student_id is not None:
            success, msg = self.enrollment_service.re_enroll_student_embeddings(
                self.re_enroll_student_id,
                self.captured_rgb_features,
                self.captured_ir_features if ir_count > 0 else None,
                pose_tags=pose_tags
            )
            if success:
                self._update_stepper_ui(2)
                self.summary_label.setText("Face Re-Enrollment Successful")
                summary_text = (
                    f"Face biometric data for {student_name} ({student_number}) updated with "
                    f"{rgb_count} RGB and {ir_count} IR multi-angle samples in {department} ({academic_year})."
                    if ir_count > 0 else
                    f"Face biometric data for {student_name} ({student_number}) updated with "
                    f"{rgb_count} RGB multi-angle samples in {department} ({academic_year})."
                )
                self.details_label.setText(summary_text)
                self.wizard_stack.setCurrentIndex(2)
            else:
                QMessageBox.critical(self, "Re-Enrollment Error", msg)
        else:
            student = Student(
                student_number=student_number,
                name=student_name,
                department=department,
                year=academic_year
            )
            success, msg = self.enrollment_service.register_student_with_embeddings(
                student,
                self.captured_rgb_features,
                self.captured_ir_features if ir_count > 0 else None,
                pose_tags=pose_tags
            )
            if success:
                self._save_avatar(student_number)
                self.enrollment_complete.emit()
                self._update_stepper_ui(2)
                self.summary_label.setText("Student Registration Successful")
                summary_text = (
                    f"{student.name} ({student.student_number}) registered successfully with "
                    f"{rgb_count} RGB and {ir_count} IR samples in {department} for academic year {academic_year}."
                    if ir_count > 0 else
                    f"{student.name} ({student.student_number}) registered successfully with "
                    f"{rgb_count} RGB samples in {department} for academic year {academic_year}."
                )
                self.details_label.setText(summary_text)
                self.wizard_stack.setCurrentIndex(2)
            else:
                QMessageBox.critical(self, "Registration Error", msg)

    def _save_avatar(self, student_number: str):
        """Save high-quality cropped frontal face avatar from the first capture sample."""
        try:
            import os
            import cv2
            avatar_dir = os.path.join(settings.BASE_DIR, "data", "avatars")
            os.makedirs(avatar_dir, exist_ok=True)
            
            frame = getattr(self, "first_rgb_capture_frame", None)
            if frame is None or frame.size == 0:
                frame = self.current_rgb_frame
            
            if frame is not None and frame.size > 0:
                avatar_path = os.path.join(avatar_dir, f"{student_number}.jpg")
                
                # Detect face and crop high-quality square frontal portrait
                faces = self.enrollment_service.detector.detect(frame)
                if faces:
                    x, y, w, h = faces[0].bbox
                    fh, fw = frame.shape[:2]
                    
                    # 45% margin for natural headshot
                    cx, cy = x + w / 2.0, y + h / 2.0
                    box_size = int(max(w, h) * 1.45)
                    
                    x1 = max(0, int(cx - box_size / 2.0))
                    y1 = max(0, int(cy - box_size / 2.0))
                    x2 = min(fw, int(cx + box_size / 2.0))
                    y2 = min(fh, int(cy + box_size / 2.0))
                    
                    cropped = frame[y1:y2, x1:x2]
                    if cropped.size > 0:
                        square_avatar = cv2.resize(cropped, (200, 200), interpolation=cv2.INTER_LANCZOS4)
                        cv2.imwrite(avatar_path, square_avatar)
                        return
                
                # Fallback: write frame
                cv2.imwrite(avatar_path, frame)
        except Exception:
            pass

    def _reset_wizard(self):
        self.re_enroll_student_id = None
        self.title_label.setText("Register Student")
        self.input_num.setEnabled(True)
        self.input_num.clear()
        self.input_name.clear()
        if settings.default_department in DEFAULT_DEPARTMENTS:
            self.input_dept.setCurrentText(settings.default_department)
        if settings.default_academic_year in DEFAULT_ACADEMIC_YEARS:
            self.input_year.setCurrentText(settings.default_academic_year)
        self.captured_rgb_features.clear()
        self.captured_ir_features.clear()
        self.capture_stage = "rgb"
        self.current_pose_idx = 0
        self._update_pose_pills()
        self._update_stepper_ui(0)
        self.wizard_stack.setCurrentIndex(0)
