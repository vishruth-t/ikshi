import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QStackedWidget, QFormLayout, QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Slot
from ui.widgets.camera_view import CameraViewWidget
from enrollment.enrollment_service import EnrollmentService
from database.models import Student, RecognitionResult
from vision.image_utils import validate_face_sample
from config.constants import DEFAULT_ACADEMIC_YEARS, DEFAULT_DEPARTMENTS
from config.settings import settings

class RegistrationPage(QWidget):
    def __init__(self, enrollment_service: EnrollmentService, parent=None):
        super().__init__(parent)
        self.enrollment_service = enrollment_service
        self.camera_view = CameraViewWidget(self)
        self.captured_features = []
        self.current_frame = None
        self.re_enroll_student_id = None

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
        self.step_label_2 = QLabel("2. Face Capture (5 Samples)")
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

    def _update_stepper_ui(self, current_step: int):
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

    @Slot(np.ndarray)
    def handle_camera_frame(self, frame: np.ndarray):
        if frame is None:
            return
        self.current_frame = frame

        # Only process & render video feed if user is on Step 2 (Capture step)
        if self.wizard_stack.currentIndex() == 1:
            frame_display = frame.copy()
            if self.enrollment_service.detector and self.enrollment_service.detector.is_loaded():
                faces = self.enrollment_service.detector.detect(frame)
                is_valid, title, subtitle = validate_face_sample(frame, faces[0].bbox if faces else (0,0,0,0), len(faces))
                
                # Dynamic visual feedback
                self.prompt_title_label.setText(title)
                self.prompt_sub_label.setText(subtitle)
                
                if is_valid:
                    self.prompt_title_label.setStyleSheet("color: #3FB950; font-weight: 700; font-size: 13px; border: none; background: transparent;")
                    self.btn_capture.setEnabled(True)
                else:
                    self.prompt_title_label.setStyleSheet("color: #E3B341; font-weight: 700; font-size: 13px; border: none; background: transparent;")

                results = []
                for face in faces:
                    res = RecognitionResult(
                        name=title if not is_valid else "Target Ready",
                        similarity=face.score,
                        bbox=face.bbox,
                        confirmed=is_valid
                    )
                    results.append(res)
                self.camera_view.update_recognition_results(results)

            self.camera_view.update_frame(frame_display)

    def _init_step1_info(self):
        step1 = QWidget()
        l = QVBoxLayout(step1)
        l.setContentsMargins(0, 8, 0, 0)
        l.setSpacing(14)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 18px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        desc = QLabel("Enter the student's biographical and academic details to begin registration.")
        desc.setStyleSheet("color: #8B949E; font-size: 13px; border: none; background: transparent;")
        card_layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(12)

        input_style = """
            QLineEdit, QComboBox {
                background-color: #0D1117;
                color: #F0F6FC;
                border: 1px solid #30363D;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #cba6f7;
            }
        """

        self.input_num = QLineEdit()
        self.input_num.setPlaceholderText("e.g. STU-2026-001")
        self.input_num.setStyleSheet(input_style)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Darshan Sharma")
        self.input_name.setStyleSheet(input_style)

        # Department Dropdown
        self.input_dept = QComboBox()
        self.input_dept.addItems(DEFAULT_DEPARTMENTS)
        self.input_dept.setCurrentText(settings.default_department if settings.default_department in DEFAULT_DEPARTMENTS else DEFAULT_DEPARTMENTS[0])
        self.input_dept.setStyleSheet(input_style)

        # Academic Year Dropdown
        self.input_year = QComboBox()
        self.input_year.addItems(DEFAULT_ACADEMIC_YEARS)
        self.input_year.setCurrentText(settings.default_academic_year if settings.default_academic_year in DEFAULT_ACADEMIC_YEARS else DEFAULT_ACADEMIC_YEARS[0])
        self.input_year.setStyleSheet(input_style)

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


        l.addWidget(card)
        l.addStretch()
        self.wizard_stack.addWidget(step1)

    def _init_step2_capture(self):
        step2 = QWidget()
        l = QVBoxLayout(step2)
        l.setContentsMargins(0, 8, 0, 0)
        l.setSpacing(10)

        # Dynamic Actionable Guidance Card
        guide_card = QFrame()
        guide_card.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 10px 14px;
            }
        """)
        g_layout = QVBoxLayout(guide_card)
        g_layout.setContentsMargins(8, 6, 8, 6)
        g_layout.setSpacing(2)

        header_line = QHBoxLayout()
        self.prompt_title_label = QLabel("Position your face inside the guide")
        self.prompt_title_label.setStyleSheet("color: #E3B341; font-weight: 700; font-size: 13px; border: none; background: transparent;")
        
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
        header_line.addWidget(self.samples_counter_badge)
        g_layout.addLayout(header_line)

        self.prompt_sub_label = QLabel("Move closer or farther away until your face is centered inside the frame.")
        self.prompt_sub_label.setStyleSheet("color: #8B949E; font-size: 12px; border: none; background: transparent;")
        g_layout.addWidget(self.prompt_sub_label)

        l.addWidget(guide_card)

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

        self.btn_capture = QPushButton("Capture Face Sample")
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
                padding: 24px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setAlignment(Qt.AlignCenter)
        c_layout.setSpacing(12)

        self.summary_label = QLabel("Registration Complete")
        self.summary_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #3FB950; background: transparent; border: none;")
        c_layout.addWidget(self.summary_label, alignment=Qt.AlignCenter)

        self.details_label = QLabel("")
        self.details_label.setStyleSheet("font-size: 13px; color: #8B949E; background: transparent; border: none; text-align: center;")
        self.details_label.setWordWrap(True)
        c_layout.addWidget(self.details_label, alignment=Qt.AlignCenter)

        btn_finish = QPushButton("Register Another Student")
        btn_finish.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7;
                color: #11111B;
                font-weight: 700;
                font-size: 13px;
                padding: 9px 20px;
                border-radius: 6px;
                border: 1px solid #cba6f7;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        btn_finish.clicked.connect(self._reset_wizard)
        c_layout.addWidget(btn_finish, alignment=Qt.AlignCenter)


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

        self.captured_features.clear()
        self.progress_bar.setValue(0)
        self.samples_counter_badge.setText("0 / 5 Samples")
        self.prompt_title_label.setText("Position your face inside the guide")
        self.prompt_sub_label.setText("Move closer or farther away until your face is centered inside the frame.")
        self._update_stepper_ui(1)
        self.wizard_stack.setCurrentIndex(1)

    def _capture_sample(self):
        if self.current_frame is None:
            self.prompt_title_label.setText("No camera frame available")
            self.prompt_sub_label.setText("Please check that your camera is connected.")
            return

        success, msg, feature = self.enrollment_service.process_sample(self.current_frame)
        if not success:
            self.prompt_title_label.setText("Capture failed")
            self.prompt_sub_label.setText(msg)
            return

        if success and feature is not None:
            self.captured_features.append(feature)
            count = len(self.captured_features)
            self.progress_bar.setValue(count)
            self.samples_counter_badge.setText(f"{count} / 5 Samples")
            
            sample_hints = [
                "Face sample 1 of 5 recorded. Please turn head slightly to the left.",
                "Face sample 2 of 5 recorded. Please turn head slightly to the right.",
                "Face sample 3 of 5 recorded. Please tilt head slightly upward.",
                "Face sample 4 of 5 recorded. Please look straight ahead.",
                "All 5 face samples captured successfully!"
            ]
            self.prompt_title_label.setText("Face sample captured")
            self.prompt_title_label.setStyleSheet("color: #3FB950; font-weight: 700; font-size: 13px; border: none; background: transparent;")
            self.prompt_sub_label.setText(sample_hints[min(count - 1, 4)])

            if count >= 5:
                self._finalize_registration()

    def _finalize_registration(self):
        student_name = self.input_name.text().strip()
        student_number = self.input_num.text().strip()
        department = self.input_dept.currentText().strip()
        academic_year = self.input_year.currentText().strip()

        if self.re_enroll_student_id is not None:
            success, msg = self.enrollment_service.re_enroll_student_embeddings(
                self.re_enroll_student_id, self.captured_features
            )
            if success:
                self._update_stepper_ui(2)
                self.summary_label.setText("Face Re-Enrollment Successful")
                self.details_label.setText(f"Face data for {student_name} ({student_number}) updated with 5 high-quality samples in {department} ({academic_year}).")
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
            success, msg = self.enrollment_service.register_student_with_embeddings(student, self.captured_features)
            if success:
                self._update_stepper_ui(2)
                self.summary_label.setText("Student Registration Successful")
                self.details_label.setText(f"{student.name} ({student.student_number}) registered successfully in {department} for academic year {academic_year}.")
                self.wizard_stack.setCurrentIndex(2)
            else:
                QMessageBox.critical(self, "Registration Error", msg)

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
        self.captured_features.clear()
        self._update_stepper_ui(0)
        self.wizard_stack.setCurrentIndex(0)
