import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QFormLayout, QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Slot
from ui.widgets.camera_view import CameraViewWidget
from enrollment.enrollment_service import EnrollmentService
from database.models import Student, RecognitionResult
from vision.image_utils import validate_face_sample

class RegistrationPage(QWidget):
    def __init__(self, enrollment_service: EnrollmentService, parent=None):
        super().__init__(parent)
        self.enrollment_service = enrollment_service
        self.camera_view = CameraViewWidget(self)
        self.captured_features = []
        self.current_frame = None
        self.re_enroll_student_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header Title
        header_row = QHBoxLayout()
        self.title_label = QLabel("STUDENT FACE ENROLLMENT WIZARD")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;")
        header_row.addWidget(self.title_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Horizontal Stepper Indicator
        self.stepper_container = QFrame()
        self.stepper_container.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 12px;
                padding: 6px 16px;
            }
        """)
        stepper_layout = QHBoxLayout(self.stepper_container)
        stepper_layout.setContentsMargins(12, 6, 12, 6)

        self.step_label_1 = QLabel("1. Student Details")
        self.step_label_2 = QLabel("2. Biometric Capture (5 Samples)")
        self.step_label_3 = QLabel("3. Complete")

        self.step_labels = [self.step_label_1, self.step_label_2, self.step_label_3]
        for i, lbl in enumerate(self.step_labels):
            stepper_layout.addWidget(lbl)
            if i < 2:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #475569; font-weight: bold;")
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
                    color: #38BDF8;
                    font-weight: 800;
                    font-size: 13px;
                    background-color: rgba(56, 189, 248, 0.15);
                    border: 1px solid rgba(56, 189, 248, 0.3);
                    border-radius: 8px;
                    padding: 4px 12px;
                """)
            elif idx < current_step:
                lbl.setStyleSheet("color: #34D399; font-weight: 700; font-size: 12px; padding: 4px 8px;")
            else:
                lbl.setStyleSheet("color: #64748B; font-weight: 500; font-size: 12px; padding: 4px 8px;")

    def load_for_re_enroll(self, student: Student):
        """Pre-populate wizard for re-enrolling an existing student's face embeddings."""
        self._reset_wizard()
        self.re_enroll_student_id = student.id
        self.title_label.setText(f"RE-ENROLL FACE EMBEDDINGS — {student.name.upper()}")
        self.input_num.setText(student.student_number)
        self.input_num.setEnabled(False)
        self.input_name.setText(student.name)
        self.input_dept.setText(student.department)
        self.input_year.setText(student.year)
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
                results = []
                for face in faces:
                    is_valid, msg = validate_face_sample(frame, face.bbox, len(faces))
                    res = RecognitionResult(
                        name="Sample Target" if is_valid else "Adjust Position",
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
        l.setContentsMargins(0, 10, 0, 0)
        l.setSpacing(16)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #111827);
                border: 1px solid #334155;
                border-radius: 14px;
                padding: 24px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        desc = QLabel("Enter the student's biographical and academic details below to begin biometric enrollment.")
        desc.setStyleSheet("color: #94A3B8; font-size: 13px; border: none; background: transparent;")
        card_layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(14)

        input_style = """
            QLineEdit {
                background-color: #090D16;
                color: #F8FAFC;
                border: 1px solid #334155;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """

        self.input_num = QLineEdit()
        self.input_num.setPlaceholderText("e.g. STU-2026-001")
        self.input_num.setStyleSheet(input_style)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Darshan Sharma")
        self.input_name.setStyleSheet(input_style)

        self.input_dept = QLineEdit()
        self.input_dept.setPlaceholderText("e.g. Computer Science & Engineering")
        self.input_dept.setStyleSheet(input_style)

        self.input_year = QLineEdit()
        self.input_year.setPlaceholderText("e.g. 3rd Year")
        self.input_year.setStyleSheet(input_style)

        def make_form_lbl(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #CBD5E1; font-weight: 600; font-size: 12px; border: none; background: transparent;")
            return lbl

        form.addRow(make_form_lbl("Student ID / Roll Number:"), self.input_num)
        form.addRow(make_form_lbl("Full Name:"), self.input_name)
        form.addRow(make_form_lbl("Department:"), self.input_dept)
        form.addRow(make_form_lbl("Academic Year:"), self.input_year)
        card_layout.addLayout(form)

        btn_next = QPushButton("Proceed to Face Capture →")
        btn_next.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                color: white;
                font-weight: 700;
                font-size: 13px;
                padding: 12px 24px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
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
        l.setContentsMargins(0, 10, 0, 0)
        l.setSpacing(12)

        # Guidance Card
        guide_card = QFrame()
        guide_card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 12px;
                padding: 10px 16px;
            }
        """)
        g_layout = QHBoxLayout(guide_card)
        g_layout.setContentsMargins(12, 8, 12, 8)

        self.quality_feedback_label = QLabel("🎯 Position face inside the camera frame and click 'Capture Face Sample'.")
        self.quality_feedback_label.setStyleSheet("color: #F59E0B; font-weight: 700; font-size: 13px; border: none; background: transparent;")
        g_layout.addWidget(self.quality_feedback_label)
        g_layout.addStretch()

        self.samples_counter_badge = QLabel("0 / 5 SAMPLES")
        self.samples_counter_badge.setStyleSheet("""
            background-color: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 800;
        """)
        g_layout.addWidget(self.samples_counter_badge)
        l.addWidget(guide_card)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #1E293B;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                border-radius: 3px;
            }
        """)
        l.addWidget(self.progress_bar)

        # Camera View
        l.addWidget(self.camera_view, stretch=1)

        # Action Buttons Row
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        btn_cancel = QPushButton("← Back to Details")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                padding: 11px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: white;
            }
        """)
        btn_cancel.clicked.connect(lambda: [self._update_stepper_ui(0), self.wizard_stack.setCurrentIndex(0)])

        self.btn_capture = QPushButton("📸 Capture Face Sample")
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                color: white;
                font-weight: 800;
                font-size: 13px;
                padding: 11px 24px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
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
        l.setContentsMargins(0, 20, 0, 0)
        l.setSpacing(20)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #111827);
                border: 1px solid rgba(16, 185, 129, 0.4);
                border-radius: 14px;
                padding: 32px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setAlignment(Qt.AlignCenter)
        c_layout.setSpacing(16)

        icon = QLabel("✅")
        icon.setStyleSheet("font-size: 44px; background: transparent; border: none;")
        c_layout.addWidget(icon, alignment=Qt.AlignCenter)

        self.summary_label = QLabel("Biometric Registration Complete!")
        self.summary_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #10B981; background: transparent; border: none;")
        c_layout.addWidget(self.summary_label, alignment=Qt.AlignCenter)

        self.details_label = QLabel("")
        self.details_label.setStyleSheet("font-size: 13px; color: #CBD5E1; background: transparent; border: none; text-align: center;")
        self.details_label.setWordWrap(True)
        c_layout.addWidget(self.details_label, alignment=Qt.AlignCenter)

        btn_finish = QPushButton("Finish & Enroll Another Student")
        btn_finish.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                color: white;
                font-weight: 700;
                font-size: 13px;
                padding: 12px 28px;
                border-radius: 8px;
                border: none;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
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
        if not num or not name:
            QMessageBox.warning(self, "Validation Error", "Please provide both Student ID and Full Name.")
            return
        self.captured_features.clear()
        self.progress_bar.setValue(0)
        self.samples_counter_badge.setText("0 / 5 SAMPLES")
        self.quality_feedback_label.setText("🎯 Position face inside the camera frame and click 'Capture Face Sample'.")
        self._update_stepper_ui(1)
        self.wizard_stack.setCurrentIndex(1)

    def _capture_sample(self):
        if self.current_frame is None:
            self.quality_feedback_label.setText("⚠️ No camera frame available.")
            return

        success, msg, feature = self.enrollment_service.process_sample(self.current_frame)
        self.quality_feedback_label.setText(f"ℹ️ {msg}")

        if success and feature is not None:
            self.captured_features.append(feature)
            count = len(self.captured_features)
            self.progress_bar.setValue(count)
            self.samples_counter_badge.setText(f"{count} / 5 SAMPLES")
            
            sample_hints = ["slight left angle", "slight right angle", "different expression", "slight tilt", "straight ahead"]
            hint_idx = min(count, 4)
            self.quality_feedback_label.setText(f"✓ Sample {count}/5 captured! Next: turn head {sample_hints[hint_idx]}.")

            if count >= 5:
                self._finalize_registration()

    def _finalize_registration(self):
        student_name = self.input_name.text().strip()
        student_number = self.input_num.text().strip()

        if self.re_enroll_student_id is not None:
            success, msg = self.enrollment_service.re_enroll_student_embeddings(
                self.re_enroll_student_id, self.captured_features
            )
            if success:
                self._update_stepper_ui(2)
                self.summary_label.setText("Face Re-Enrollment Successful!")
                self.details_label.setText(f"Successfully re-enrolled 128D OpenCV SFace biometric embeddings for {student_name} ({student_number}) with {len(self.captured_features)} high-quality samples.")
                self.wizard_stack.setCurrentIndex(2)
            else:
                QMessageBox.critical(self, "Re-Enrollment Error", msg)
        else:
            student = Student(
                student_number=student_number,
                name=student_name,
                department=self.input_dept.text().strip() or "General",
                year=self.input_year.text().strip() or "1st Year"
            )
            success, msg = self.enrollment_service.register_student_with_embeddings(student, self.captured_features)
            if success:
                self._update_stepper_ui(2)
                self.summary_label.setText("Student Registration Successful!")
                self.details_label.setText(f"Successfully registered {student.name} ({student.student_number}) with {len(self.captured_features)} OpenCV SFace feature vectors in database.")
                self.wizard_stack.setCurrentIndex(2)
            else:
                QMessageBox.critical(self, "Registration Error", msg)

    def _reset_wizard(self):
        self.re_enroll_student_id = None
        self.title_label.setText("STUDENT FACE ENROLLMENT WIZARD")
        self.input_num.setEnabled(True)
        self.input_num.clear()
        self.input_name.clear()
        self.input_dept.clear()
        self.input_year.clear()
        self.captured_features.clear()
        self._update_stepper_ui(0)
        self.wizard_stack.setCurrentIndex(0)


