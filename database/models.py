from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import numpy as np

@dataclass
class Student:
    id: Optional[int] = None
    student_number: str = ""
    name: str = ""
    department: str = ""
    year: str = ""
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class FaceEmbedding:
    id: Optional[int] = None
    student_id: int = 0
    embedding: np.ndarray = field(default_factory=lambda: np.zeros((1, 128), dtype=np.float32))
    model_name: str = "SFace"
    model_version: str = "2021dec"
    metric: str = "cosine"
    pose_tag: str = "frontal"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class AttendanceSession:
    id: Optional[int] = None
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    subject: str = ""
    class_name: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None

@dataclass
class Attendance:
    id: Optional[int] = None
    session_id: int = 0
    student_id: int = 0
    marked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "Present"
    similarity: float = 0.0
    liveness_score: Optional[float] = None
    liveness_passed: Optional[bool] = None

@dataclass
class RecognitionResult:
    student_id: Optional[int] = None
    student_number: Optional[str] = None
    name: Optional[str] = None
    similarity: float = 0.0
    metric: str = "cosine"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    bbox: Optional[tuple] = None # (x, y, w, h)
    confirmed: bool = False
    liveness_score: Optional[float] = None
    liveness_passed: Optional[bool] = None
    liveness_status: str = "disabled" # "disabled", "checking", "passed", "failed"
    liveness_message: str = ""
    ir_bbox: Optional[tuple] = None
    matched_pose: Optional[str] = None

@dataclass
class SecurityAudit:
    id: Optional[int] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    matched_student_id: Optional[int] = None
    matched_name: Optional[str] = None
    reason: str = ""
    liveness_score: float = 0.0
    texture_score: float = 0.0
    reflectance_score: float = 0.0
    entropy_score: float = 0.0
    motion_score: float = 0.0
    snapshot_path: Optional[str] = None
    ir_snapshot_path: Optional[str] = None
