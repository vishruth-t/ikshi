"""
ikshi - Infrared (IR) Anti-Spoofing & Liveness Detection Module
===============================================================

Physical Context & Architecture:
--------------------------------
This module implements a local, lightweight, heuristic anti-spoofing layer
utilizing flat 2D infrared intensity frames (e.g. 8-bit greyscale from V4L2 GREY sensors
found in Windows Hello webcams like /dev/video2 at 640x360).

NON-GOALS & PHYSICAL LIMITATIONS (IMPORTANT):
--------------------------------------------
1. NO STRUCTURED LIGHT / DEPTH PROJECTOR:
   This module processes flat 2D infrared reflectance, NOT 3D structured light
   or Time-of-Flight (ToF) depth maps. It does not claim cryptographic-grade
   biometric liveness.
2. THREAT MODEL:
   Designed specifically to block casual physical spoofing vectors:
     - Printed 2D paper photos held up to the camera (flat IR reflectance, absence of 3D facial gradients).
     - Smartphone / tablet / laptop screens displaying photos/videos (IR absorption blackout, polarizing glare, absence of natural skin reflectance).
3. RESIDUAL RISK:
   A sophisticated attack (such as high-end silicone masks, custom IR-matched printed media,
   or another live accomplice) cannot be ruled out by flat 2D intensity heuristics alone.
4. GRACEFUL DEGRADATION:
   If the secondary IR camera hardware is missing or fails to open, the application
   logs a clear warning and seamlessly degrades to RGB-only operation without blocking
   or crashing the attendance pipeline.
"""

import cv2
import time
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any, List
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LivenessResult:
    """Result of IR anti-spoofing liveness analysis."""
    passed: bool
    score: float # Normalized score between 0.0 and 1.0
    texture_score: float
    reflectance_score: float
    motion_score: float
    status: str # "passed", "failed", "checking", "disabled", "error"
    message: str # User-facing status description
    ir_bbox: Optional[Tuple[int, int, int, int]] = None
    details: Dict[str, Any] = field(default_factory=dict)


class IRLivenessDetector:
    """
    Heuristic Anti-Spoofing and Liveness Analyzer using Infrared (IR) intensity frames.
    Combines:
      1. Texture & Sharpness Analysis (Laplacian Variance in IR)
      2. Reflectance & Dynamic Range Sanity Check (Skin vs Screen/Glare/Blackout)
      3. Temporal Micro-Movement Variance (Tracking natural micro-tremor vs static prints)
    """

    def __init__(self, history_size: int = 5):
        self.history_size = history_size
        # Track recent IR crops per identity / track_id for temporal motion analysis
        self._history: Dict[Any, List[np.ndarray]] = {}

    def map_bbox_to_ir(
        self,
        rgb_bbox: Tuple[int, int, int, int],
        rgb_shape: Tuple[int, int],
        ir_shape: Tuple[int, int]
    ) -> Tuple[int, int, int, int]:
        """
        Maps a bounding box from RGB camera coordinate space to secondary IR sensor space.
        Applies FOV scaling and pixel offset adjustments from settings.
        
        Args:
            rgb_bbox: (x, y, w, h) in RGB frame.
            rgb_shape: (height, width) of RGB frame.
            ir_shape: (height, width) of IR frame.
            
        Returns:
            (ir_x, ir_y, ir_w, ir_h) clamped within IR frame boundaries.
        """
        rgb_h, rgb_w = rgb_shape[:2]
        ir_h, ir_w = ir_shape[:2]

        x, y, w, h = rgb_bbox
        
        # Center of face in normalized coordinates [0.0, 1.0]
        norm_cx = (x + w / 2.0) / max(1, rgb_w)
        norm_cy = (y + h / 2.0) / max(1, rgb_h)
        norm_w = w / max(1, rgb_w)
        norm_h = h / max(1, rgb_h)

        scale_x = getattr(settings, "ir_fov_scale_x", 1.0)
        scale_y = getattr(settings, "ir_fov_scale_y", 1.0)
        offset_x = getattr(settings, "ir_offset_x", 0)
        offset_y = getattr(settings, "ir_offset_y", 0)

        # Projected center and size in IR pixels
        ir_cx = norm_cx * ir_w * scale_x + offset_x
        ir_cy = norm_cy * ir_h * scale_y + offset_y
        ir_bw = norm_w * ir_w * scale_x
        ir_bh = norm_h * ir_h * scale_y

        ir_x1 = int(max(0, ir_cx - ir_bw / 2.0))
        ir_y1 = int(max(0, ir_cy - ir_bh / 2.0))
        ir_x2 = int(min(ir_w, ir_cx + ir_bw / 2.0))
        ir_y2 = int(min(ir_h, ir_cy + ir_bh / 2.0))

        ir_w_box = max(1, ir_x2 - ir_x1)
        ir_h_box = max(1, ir_y2 - ir_y1)

        return (ir_x1, ir_y1, ir_w_box, ir_h_box)

    def extract_ir_face(
        self,
        ir_frame: np.ndarray,
        ir_bbox: Tuple[int, int, int, int]
    ) -> Optional[np.ndarray]:
        """
        Extracts single-channel 8-bit grayscale face crop from the IR frame.
        Handles OpenCV V4L2 3-channel GREY conversions by reading channel 0.
        """
        if ir_frame is None or ir_frame.size == 0:
            return None

        # Convert / extract single-channel grayscale
        if len(ir_frame.shape) == 3 and ir_frame.shape[2] == 3:
            ir_gray = ir_frame[:, :, 0]
        elif len(ir_frame.shape) == 2:
            ir_gray = ir_frame
        else:
            ir_gray = cv2.cvtColor(ir_frame, cv2.COLOR_BGR2GRAY)

        x, y, w, h = ir_bbox
        h_frame, w_frame = ir_gray.shape[:2]

        x1 = max(0, min(w_frame - 1, x))
        y1 = max(0, min(h_frame - 1, y))
        x2 = max(x1 + 1, min(w_frame, x + w))
        y2 = max(y1 + 1, min(h_frame, y + h))

        crop = ir_gray[y1:y2, x1:x2]
        if crop.size < 16: # Less than 4x4
            return None
        return crop

    def _detect_device_bezels(self, ir_crop: np.ndarray) -> Tuple[float, bool, str]:
        """
        Detects straight line segments characteristic of smartphone screens, tablets, and photo frames at any angle.
        Human facial contours are smooth organic curves; mobile device bodies contain prominent straight edges.
        """
        try:
            h, w = ir_crop.shape[:2]
            if h < 20 or w < 20:
                return 1.0, False, ""

            blurred = cv2.GaussianBlur(ir_crop, (5, 5), 1.5)
            edges = cv2.Canny(blurred, 45, 130)
            # Mask out crop outer boundary so image crop borders don't falsely trigger as bezels
            b = 6
            edges[:b, :] = 0
            edges[-b:, :] = 0
            edges[:, :b] = 0
            edges[:, -b:] = 0

            min_len = int(min(h, w) * 0.38)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=25, minLineLength=min_len, maxLineGap=5)
            
            if lines is None:
                return 1.0, False, ""

            if len(lines) >= 2:
                return 0.10, True, "Spoof Detected: Phone / Device Screen Frame"
            elif len(lines) == 1:
                return 0.40, False, "Possible Straight Edge"
            return 1.0, False, ""
        except Exception as e:
            logger.debug(f"Device bezel detection error: {e}")
            return 1.0, False, ""

    def _compute_planar_intensity_ramp(self, ir_crop: np.ndarray) -> Tuple[float, str]:
        """
        Detects planar lighting gradients across horizontal turns and vertical tilts.
        When a flat glass phone is turned, one side reflects more ambient IR light than the other,
        producing a strong monotonic linear ramp across columns or rows (high R-squared).
        A real 3D human face has central bilateral symmetry (nose highlight, cheek curvature drop).
        """
        try:
            # 1. Horizontal turn / yaw analysis (column means)
            col_means = np.mean(ir_crop, axis=0)
            w = len(col_means)
            if w >= 12:
                x_coords = np.arange(w)
                slope, intercept = np.polyfit(x_coords, col_means, 1)
                fit_line = slope * x_coords + intercept
                ss_tot = np.sum((col_means - np.mean(col_means)) ** 2)
                ss_res = np.sum((col_means - fit_line) ** 2)
                r2_x = 1.0 - (ss_res / max(1e-5, ss_tot))
                drop_x = abs(slope) * w
                if r2_x > 0.82 and drop_x > 25.0:
                    return 0.10, "Spoof Detected: Planar Glass Lighting Ramp (Horizontal Turn)"

            # 2. Vertical tilt / pitch analysis (row means)
            row_means = np.mean(ir_crop, axis=1)
            h = len(row_means)
            if h >= 12:
                y_coords = np.arange(h)
                slope_y, intercept_y = np.polyfit(y_coords, row_means, 1)
                fit_line_y = slope_y * y_coords + intercept_y
                ss_tot_y = np.sum((row_means - np.mean(row_means)) ** 2)
                ss_res_y = np.sum((row_means - fit_line_y) ** 2)
                r2_y = 1.0 - (ss_res_y / max(1e-5, ss_tot_y))
                drop_y = abs(slope_y) * h
                if r2_y > 0.82 and drop_y > 25.0:
                    return 0.10, "Spoof Detected: Planar Glass Lighting Ramp (Vertical Tilt)"

            return 1.0, "Symmetric Anatomical Shading"
        except Exception as e:
            logger.debug(f"Planar ramp calculation error: {e}")
            return 1.0, "Planar Check Error"

    def _compute_gradient_entropy(self, ir_crop: np.ndarray) -> Tuple[float, str]:
        """
        Analyzes 3D facial curvature vs 2D flat planar reflection (e.g. tilted phone screen).
        A real 3D face scatters gradients radially in 360 degrees (high orientation entropy).
        A 2D phone screen has polarized planar gradients in 1 or 2 directions (low entropy).
        """
        try:
            gx = cv2.Sobel(ir_crop, cv2.CV_64F, 1, 0, ksize=3)
            gy = cv2.Sobel(ir_crop, cv2.CV_64F, 0, 1, ksize=3)
            mag = np.hypot(gx, gy)
            angles = (np.arctan2(gy, gx) * 180.0 / np.pi) % 180.0

            valid = mag > 7.0
            total_valid = np.count_nonzero(valid)
            if total_valid < 40:
                return 0.15, "Spoof Detected: Flat 2D Surface (No Depth Contours)"

            counts, _ = np.histogram(angles[valid], bins=8, range=(0.0, 180.0))
            probs = counts.astype(np.float64) / float(total_valid)
            probs = probs[probs > 0.0]
            entropy = -np.sum(probs * np.log2(probs))
            norm_entropy = float(entropy / 3.0) # log2(8) = 3.0

            # Real 3D face: norm_entropy typically 0.80 - 1.0
            # Tilted/turned screen or flat print: norm_entropy < 0.68
            if norm_entropy < 0.68:
                return 0.15, "Spoof Detected: Flat Planar Reflection (Turned Screen)"
            
            score = float(np.clip((norm_entropy - 0.65) / 0.30, 0.0, 1.0))
            return score, "Valid 3D Depth Contour"
        except Exception as e:
            logger.debug(f"Gradient entropy error: {e}")
            return 0.5, "Entropy Check Error"

    def _compute_texture_score(self, ir_crop: np.ndarray) -> float:
        """
        Computes texture sharpness variance using the Laplacian operator.
        Live skin contains fine 3D gradations and anatomical contours.
        Flat paper prints or heavily diffused surfaces show noticeably low variance.
        """
        try:
            std_crop = cv2.resize(ir_crop, (96, 96), interpolation=cv2.INTER_AREA)
            lap = cv2.Laplacian(std_crop, cv2.CV_64F)
            var = float(lap.var())

            # Normalization curve:
            # var < 18: flat / blurred (score -> 0.0)
            # var 18-90: transitional
            # var > 90: rich anatomical texture (score -> 1.0)
            score = (var - 18.0) / 72.0
            return float(np.clip(score, 0.0, 1.0))
        except Exception as e:
            logger.debug(f"Texture score calculation error: {e}")
            return 0.5

    def _compute_reflectance_score(self, ir_crop: np.ndarray) -> Tuple[float, str]:
        """
        Checks intensity distribution, contrast, and screen glare/blackout patterns.
        Screens typically produce:
          - Harsh specular glare (large proportion of saturated pixels > 240)
          - OLED/LCD blackout (mean intensity < 25, low contrast)
        """
        try:
            mean_val = float(np.mean(ir_crop))
            std_val = float(np.std(ir_crop))
            total_pixels = ir_crop.size

            glare_pixels = np.count_nonzero(ir_crop >= 240)
            glare_ratio = float(glare_pixels) / float(total_pixels)

            blackout_pixels = np.count_nonzero(ir_crop <= 15)
            blackout_ratio = float(blackout_pixels) / float(total_pixels)

            # 1. Glare detection (Screen glass reflection from phone/tablet surface)
            if glare_ratio > 0.08:
                return 0.10, "Spoof Detected: Screen Glare"

            # 2. Blackout detection (Screen absorption / turned-off display)
            if blackout_ratio > 0.35 or mean_val < 25.0:
                return 0.10, "Spoof Detected: Screen Blackout"

            # 3. Dynamic contrast check
            # Natural human skin in typical ambient IR has std_val between 15 and 65
            if std_val < 13.0:
                return 0.20, "Spoof Detected: Unnatural Flat Reflectance"

            # Smooth score based on realistic skin intensity window [35..210]
            # Gaussian bell centered around 110
            intensity_score = np.exp(-((mean_val - 110.0) ** 2) / (2 * (55.0 ** 2)))
            contrast_score = min(1.0, std_val / 28.0)

            score = float(np.clip(0.6 * intensity_score + 0.4 * contrast_score, 0.0, 1.0))
            return score, "Valid IR Reflectance"
        except Exception as e:
            logger.debug(f"Reflectance score error: {e}")
            return 0.5, "Reflectance Evaluation Error"

    def _compute_motion_score(self, ir_crop: np.ndarray, tracker_key: Any) -> float:
        """
        Computes temporal frame-to-frame variance for the candidate.
        A printed photo mounted or held still lacks live physiological micro-movement.
        """
        if tracker_key is None:
            return 0.5 # Neutral score when tracking key is not provided

        try:
            norm_crop = cv2.resize(ir_crop, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32)
            history = self._history.setdefault(tracker_key, [])

            if not history:
                history.append(norm_crop)
                return 0.5 # Neutral on first observation

            prev_crop = history[-1]
            diff = float(np.mean(np.abs(norm_crop - prev_crop)))

            # Update history ring buffer
            history.append(norm_crop)
            if len(history) > self.history_size:
                history.pop(0)

            # Live micro-movement:
            # diff < 0.20: static print held still (score -> 0.10)
            if diff < 0.20:
                return 0.10 # Static paper photo
            elif diff <= 25.0:
                score = (diff - 0.20) / 2.0
                return float(np.clip(score, 0.3, 1.0))
            else:
                return 0.7
        except Exception as e:
            logger.debug(f"Motion score error: {e}")
            return 0.5

    def evaluate(
        self,
        rgb_frame: np.ndarray,
        ir_frame: Optional[np.ndarray],
        rgb_bbox: Tuple[int, int, int, int],
        student_id: Optional[int] = None,
        enrolled_ir_embeddings: Optional[List[np.ndarray]] = None,
        sface_recognizer: Optional[Any] = None,
        face_detector: Optional[Any] = None
    ) -> LivenessResult:
        """
        Evaluate anti-spoofing liveness for a detected face bounding box using multimodal analysis.
        
        Args:
            rgb_frame: Primary RGB camera image.
            ir_frame: Secondary IR camera image (or None if IR not available).
            rgb_bbox: (x, y, w, h) bounding box from face detector.
            student_id: Optional identifier for temporal tracking.
            enrolled_ir_embeddings: Optional list of enrolled IR embeddings for candidate student.
            sface_recognizer: Optional SFaceRecognizer instance for IR biometric cross-check.
            face_detector: Optional FaceDetector (YuNet) for authentic IR landmark validation.
            
        Returns:
            LivenessResult containing score, passed flag, and diagnostic messages.
        """
        if not settings.enable_ir_liveness:
            return LivenessResult(
                passed=True,
                score=1.0,
                texture_score=1.0,
                reflectance_score=1.0,
                motion_score=1.0,
                status="disabled",
                message="IR Liveness Disabled"
            )

        if ir_frame is None or ir_frame.size == 0:
            return LivenessResult(
                passed=True, # Graceful degradation: pass through if IR hardware is not available
                score=1.0,
                texture_score=1.0,
                reflectance_score=1.0,
                motion_score=1.0,
                status="disabled",
                message="IR Sensor Feed Unavailable (RGB Fallback)"
            )

        # 1. Map RGB bbox to IR coordinate frame and extract IR crop
        ir_bbox = self.map_bbox_to_ir(rgb_bbox, rgb_frame.shape, ir_frame.shape)
        ir_crop = self.extract_ir_face(ir_frame, ir_bbox)

        if ir_crop is None:
            return LivenessResult(
                passed=False,
                score=0.0,
                texture_score=0.0,
                reflectance_score=0.0,
                motion_score=0.0,
                status="failed",
                message="Spoof Detected: No IR Face Region",
                ir_bbox=ir_bbox
            )

        # 2. Hardware IR Face Detection & Alignment Check (YuNet)
        ir_face_data = None
        if face_detector is not None and face_detector.is_loaded():
            ir_3ch = ir_frame if (len(ir_frame.shape) == 3 and ir_frame.shape[2] == 3) else cv2.cvtColor(ir_crop, cv2.COLOR_GRAY2BGR)
            if len(ir_3ch.shape) == 2:
                ir_3ch = cv2.cvtColor(ir_3ch, cv2.COLOR_GRAY2BGR)
            
            ir_faces = face_detector.detect(ir_3ch)
            if not ir_faces:
                # Phone screens and dark prints lack authentic infrared facial landmarks
                return LivenessResult(
                    passed=False,
                    score=0.05,
                    texture_score=0.0,
                    reflectance_score=0.10,
                    motion_score=0.0,
                    status="failed",
                    message="Spoof Detected: No IR Face Signature (Phone Screen / Photo)",
                    ir_bbox=ir_bbox
                )
            else:
                # Find matching face in IR frame
                ir_face_data = ir_faces[0].raw_face_data

        # 3. Phone Bezel & Screen Edge Detection
        bezel_score, has_bezels, bezel_msg = self._detect_device_bezels(ir_crop)
        if has_bezels:
            return LivenessResult(
                passed=False,
                score=0.10,
                texture_score=0.20,
                reflectance_score=0.10,
                motion_score=0.30,
                status="failed",
                message=bezel_msg,
                ir_bbox=ir_bbox
            )

        # 4. Planar Glass Lighting Ramp (Detects Horizontally Turned / Tilted Glass Surfaces)
        ramp_score, ramp_msg = self._compute_planar_intensity_ramp(ir_crop)
        if "Spoof Detected" in ramp_msg:
            return LivenessResult(
                passed=False,
                score=0.10,
                texture_score=0.20,
                reflectance_score=0.10,
                motion_score=0.30,
                status="failed",
                message=ramp_msg,
                ir_bbox=ir_bbox
            )

        # 5. 3D Gradient Orientation Entropy (Flat Glass vs 3D Face)
        entropy_score, entropy_msg = self._compute_gradient_entropy(ir_crop)
        if "Spoof Detected" in entropy_msg or entropy_score <= 0.20:
            return LivenessResult(
                passed=False,
                score=0.15,
                texture_score=0.20,
                reflectance_score=0.15,
                motion_score=0.30,
                status="failed",
                message=entropy_msg,
                ir_bbox=ir_bbox
            )

        # 6. Core Reflectance & Texture Checks
        reflectance_score, refl_msg = self._compute_reflectance_score(ir_crop)
        if "Spoof Detected" in refl_msg or reflectance_score <= 0.20:
            return LivenessResult(
                passed=False,
                score=0.10,
                texture_score=0.20,
                reflectance_score=reflectance_score,
                motion_score=0.30,
                status="failed",
                message=refl_msg,
                ir_bbox=ir_bbox
            )

        texture_score = self._compute_texture_score(ir_crop)
        motion_score = self._compute_motion_score(ir_crop, student_id)

        # 7. Strict Enrolled IR Biometric Cross-Match
        ir_biometric_score = None
        if enrolled_ir_embeddings and sface_recognizer is not None and sface_recognizer.is_loaded():
            try:
                ir_3ch = ir_frame if (len(ir_frame.shape) == 3 and ir_frame.shape[2] == 3) else cv2.cvtColor(ir_crop, cv2.COLOR_GRAY2BGR)
                if len(ir_3ch.shape) == 2:
                    ir_3ch = cv2.cvtColor(ir_3ch, cv2.COLOR_GRAY2BGR)

                if ir_face_data is not None:
                    aligned_crop = sface_recognizer.align_crop(ir_3ch, ir_face_data)
                else:
                    aligned_crop = cv2.resize(ir_crop, (112, 112), interpolation=cv2.INTER_AREA)
                    if len(aligned_crop.shape) == 2:
                        aligned_crop = cv2.cvtColor(aligned_crop, cv2.COLOR_GRAY2BGR)

                if aligned_crop is not None:
                    ir_feat = sface_recognizer.extract_feature(aligned_crop)
                    if ir_feat is not None:
                        ir_sims = [
                            sface_recognizer.match(ir_feat.reshape(1, -1), enrolled_vec.reshape(1, -1), metric="cosine")
                            for enrolled_vec in enrolled_ir_embeddings
                        ]
                        ir_biometric_score = max(ir_sims) if ir_sims else 0.0

                        # HARD BIOMETRIC REJECTION:
                        # If enrolled IR samples exist and IR cosine match < 0.35, reject as spoof!
                        if ir_biometric_score < 0.35:
                            return LivenessResult(
                                passed=False,
                                score=0.10,
                                texture_score=texture_score,
                                reflectance_score=reflectance_score,
                                motion_score=motion_score,
                                status="failed",
                                message=f"Spoof Detected: IR Biometric Mismatch ({int(ir_biometric_score * 100)}%)",
                                ir_bbox=ir_bbox,
                                details={"ir_biometric": ir_biometric_score}
                            )
            except Exception as e:
                logger.debug(f"IR biometric matching error: {e}")

        # 8. Weighted Composite Score
        # Texture: 25%, Reflectance: 30%, Entropy/3D: 25%, Motion: 20%
        composite_score = (
            0.25 * texture_score +
            0.30 * reflectance_score +
            0.25 * entropy_score +
            0.20 * motion_score
        )
        if ir_biometric_score is not None:
            # Boost composite score with authentic IR biometric match
            bio_norm = float(np.clip((ir_biometric_score - 0.35) / 0.30, 0.0, 1.0))
            composite_score = 0.40 * composite_score + 0.60 * bio_norm

        composite_score = float(np.clip(composite_score, 0.0, 1.0))

        threshold = getattr(settings, "ir_liveness_threshold", 0.55)
        passed = composite_score >= threshold

        if not passed:
            if texture_score < 0.25:
                status_msg = "Spoof Detected: Flat 2D Texture"
            elif motion_score < 0.20:
                status_msg = "Spoof Detected: Static Photo"
            elif entropy_score < 0.40:
                status_msg = "Spoof Detected: Flat Planar Surface"
            else:
                status_msg = f"Liveness Failed ({int(composite_score * 100)}% < {int(threshold * 100)}%)"
            status = "failed"
        else:
            status_msg = f"Liveness Passed ({int(composite_score * 100)}%)"
            status = "passed"

        return LivenessResult(
            passed=passed,
            score=composite_score,
            texture_score=texture_score,
            reflectance_score=reflectance_score,
            motion_score=motion_score,
            status=status,
            message=status_msg,
            ir_bbox=ir_bbox,
            details={
                "threshold": threshold,
                "texture": texture_score,
                "reflectance": reflectance_score,
                "entropy": entropy_score,
                "motion": motion_score,
                "ir_biometric": ir_biometric_score
            }
        )

    def reset_history(self, student_id: Optional[int] = None):
        """Reset temporal tracking history."""
        if student_id is not None:
            self._history.pop(student_id, None)
        else:
            self._history.clear()
