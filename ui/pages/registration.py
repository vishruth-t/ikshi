import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QFormLayout, QProgressBar, QMessageBox
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
        layout.setContentsMargins(20, 20, 20, 20)

        self.title_label = QLabel("STUDENT FACE ENROLLMENT WIZARD")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(self.title_label)

        # Wizard Step Stack
        self.wizard_stack = QStackedWidget()
        layout.addWidget(self.wizard_stack)

        # Build Wizard Steps
        self._init_step1_info()
        self._init_step2_capture()
        self._init_step3_complete()

        self.wizard_stack.setCurrentIndex(0)

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
            # Perform live face detection overlay for real-time visual feedback
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
        l.setSpacing(15)

        lbl = QLabel("Step 1: Student Metadata")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")
        l.addWidget(lbl)

        form = QFormLayout()
        self.input_num = QLineEdit()
        self.input_num.setPlaceholderText("e.g. STU-2026-001")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Darshan Sharma")
        self.input_dept = QLineEdit()
        self.input_dept.setPlaceholderText("e.g. Computer Science")
        self.input_year = QLineEdit()
        self.input_year.setPlaceholderText("e.g. 3rd Year")

        for input_field in [self.input_num, self.input_name, self.input_dept, self.input_year]:
            input_field.setStyleSheet("background-color: #1E293B; color: white; border: 1px solid #334155; padding: 8px; border-radius: 6px;")

        form.addRow("Student ID / Number:", self.input_num)
        form.addRow("Full Name:", self.input_name)
        form.addRow("Department:", self.input_dept)
        form.addRow("Academic Year:", self.input_year)
        l.addLayout(form)

        btn_next = QPushButton("Next: Face Enrollment →")
        btn_next.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_next.clicked.connect(self._goto_step2)
        l.addWidget(btn_next, alignment=Qt.AlignRight)
        l.addStretch()

        self.wizard_stack.addWidget(step1)

    def _init_step2_capture(self):
        step2 = QWidget()
        l = QVBoxLayout(step2)
        l.setSpacing(10)

        lbl = QLabel("Step 2: Capture Face Samples (5 samples required)")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")
        l.addWidget(lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 5px;
                text-align: center;
                background-color: #1E293B;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #10B981;
            }
        """)
        l.addWidget(self.progress_bar)

        self.quality_feedback_label = QLabel("Position face in camera frame and click 'Capture Sample'.")
        self.quality_feedback_label.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 14px;")
        l.addWidget(self.quality_feedback_label)

        l.addWidget(self.camera_view, stretch=1)

        btn_box = QHBoxLayout()
        self.btn_capture = QPushButton("📷 Capture Face Sample")
        self.btn_capture.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        self.btn_capture.clicked.connect(self._capture_sample)

        btn_cancel = QPushButton("← Back")
        btn_cancel.setStyleSheet("background-color: #475569; color: white; padding: 10px; border-radius: 6px;")
        btn_cancel.clicked.connect(lambda: self.wizard_stack.setCurrentIndex(0))

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_capture)
        l.addLayout(btn_box)

        self.wizard_stack.addWidget(step2)

    def _init_step3_complete(self):
        step3 = QWidget()
        l = QVBoxLayout(step3)
        l.setSpacing(20)

        self.summary_label = QLabel("Step 3: Registration Complete!")
        self.summary_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
        l.addWidget(self.summary_label)

        self.details_label = QLabel("")
        self.details_label.setStyleSheet("font-size: 14px; color: #CBD5E1;")
        l.addWidget(self.details_label)

        btn_finish = QPushButton("Finish & Enroll New Student")
        btn_finish.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_finish.clicked.connect(self._reset_wizard)
        l.addWidget(btn_finish)
        l.addStretch()

        self.wizard_stack.addWidget(step3)

    def _goto_step2(self):
        num = self.input_num.text().strip()
        name = self.input_name.text().strip()
        if not num or not name:
            QMessageBox.warning(self, "Validation Error", "Please fill in Student ID and Full Name.")
            return
        self.captured_features.clear()
        self.progress_bar.setValue(0)
        self.quality_feedback_label.setText("Position face in camera frame and click 'Capture Sample'.")
        self.wizard_stack.setCurrentIndex(1)

    def _capture_sample(self):
        if self.current_frame is None:
            self.quality_feedback_label.setText("No camera frame available.")
            return

        success, msg, feature = self.enrollment_service.process_sample(self.current_frame)
        self.quality_feedback_label.setText(msg)

        if success and feature is not None:
            self.captured_features.append(feature)
            self.progress_bar.setValue(len(self.captured_features))
            sample_hints = ["slight left", "slight right", "different expression", "slight tilt", "straight ahead"]
            hint_idx = min(len(self.captured_features), 4)
            self.quality_feedback_label.setText(f"Sample {len(self.captured_features)}/5 captured! Next: turn head {sample_hints[hint_idx]}.")

            if len(self.captured_features) >= 5:
                self._finalize_registration()

    def _finalize_registration(self):
        student_name = self.input_name.text().strip()
        student_number = self.input_num.text().strip()

        if self.re_enroll_student_id is not None:
            # Re-enrollment path
            success, msg = self.enrollment_service.re_enroll_student_embeddings(
                self.re_enroll_student_id, self.captured_features
            )
            if success:
                self.summary_label.setText("Step 3: Face Re-Enrollment Complete!")
                self.details_label.setText(f"Successfully re-enrolled face embeddings for {student_name} ({student_number}) with {len(self.captured_features)} updated biometric feature vectors.")
                self.wizard_stack.setCurrentIndex(2)
            else:
                QMessageBox.critical(self, "Re-Enrollment Error", msg)
        else:
            # New student registration path
            student = Student(
                student_number=student_number,
                name=student_name,
                department=self.input_dept.text().strip() or "General",
                year=self.input_year.text().strip() or "1st Year"
            )
            success, msg = self.enrollment_service.register_student_with_embeddings(student, self.captured_features)
            if success:
                self.summary_label.setText("Step 3: Registration Complete!")
                self.details_label.setText(f"Successfully registered {student.name} ({student.student_number}) with {len(self.captured_features)} face feature vectors stored.")
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
        self.wizard_stack.setCurrentIndex(0)

