import sqlite3
import numpy as np
import logging
from typing import List, Optional, Tuple, Dict, Any
from database.connection import DatabaseConnection
from database.models import Student, FaceEmbedding, AttendanceSession, Attendance

logger = logging.getLogger(__name__)

class StudentRepository:
    def __init__(self, db_conn: DatabaseConnection):
        self.db = db_conn

    def create(self, student: Student) -> Student:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO students (student_number, name, department, year, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (student.student_number, student.name, student.department, student.year, 1 if student.active else 0, student.created_at, student.updated_at)
            )
            student.id = cursor.lastrowid
            conn.commit()
        return student

    def update(self, student: Student) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE students
                SET student_number = ?, name = ?, department = ?, year = ?, active = ?, updated_at = ?
                WHERE id = ?
                """,
                (student.student_number, student.name, student.department, student.year, 1 if student.active else 0, student.updated_at, student.id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def set_active(self, student_id: int, active: bool) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET active = ? WHERE id = ?", (1 if active else 0, student_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, student_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            return cursor.rowcount > 0


    def get_by_id(self, student_id: int) -> Optional[Student]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            if row:
                return Student(
                    id=row["id"],
                    student_number=row["student_number"],
                    name=row["name"],
                    department=row["department"],
                    year=row["year"],
                    active=bool(row["active"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None

    def get_by_number(self, student_number: str) -> Optional[Student]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE student_number = ?", (student_number,))
            row = cursor.fetchone()
            if row:
                return Student(
                    id=row["id"],
                    student_number=row["student_number"],
                    name=row["name"],
                    department=row["department"],
                    year=row["year"],
                    active=bool(row["active"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None

    def get_all(self, active_only: bool = False) -> List[Student]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM students"
            params = []
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY name ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                Student(
                    id=r["id"],
                    student_number=r["student_number"],
                    name=r["name"],
                    department=r["department"],
                    year=r["year"],
                    active=bool(r["active"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                )
                for r in rows
            ]


class FaceEmbeddingRepository:
    def __init__(self, db_conn: DatabaseConnection):
        self.db = db_conn

    def add_embedding(self, embedding: FaceEmbedding) -> FaceEmbedding:
        blob_data = embedding.embedding.astype(np.float32).tobytes()
        pose_tag = getattr(embedding, "pose_tag", "frontal") or "frontal"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO face_embeddings (student_id, embedding, model_name, model_version, metric, pose_tag, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (embedding.student_id, blob_data, embedding.model_name, embedding.model_version, embedding.metric, pose_tag, embedding.created_at)
            )
            embedding.id = cursor.lastrowid
            conn.commit()
        return embedding

    def delete_embeddings_for_student(self, student_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM face_embeddings WHERE student_id = ?", (student_id,))
            conn.commit()

    def get_all_embeddings(self, model_name: Optional[str] = None) -> List[Tuple[int, str, str, np.ndarray, str]]:
        """
        Returns list of (student_id, student_number, student_name, embedding_vector, pose_tag)
        for all active students. Optionally filters by model_name (e.g. 'SFace' vs 'SFace-IR').
        """
        results = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if model_name:
                cursor.execute(
                    """
                    SELECT e.student_id, s.student_number, s.name, e.embedding, COALESCE(e.pose_tag, 'frontal') AS pose_tag
                    FROM face_embeddings e
                    JOIN students s ON e.student_id = s.id
                    WHERE s.active = 1 AND e.model_name = ?
                    """,
                    (model_name,)
                )
            else:
                cursor.execute(
                    """
                    SELECT e.student_id, s.student_number, s.name, e.embedding, COALESCE(e.pose_tag, 'frontal') AS pose_tag
                    FROM face_embeddings e
                    JOIN students s ON e.student_id = s.id
                    WHERE s.active = 1
                    """
                )
            rows = cursor.fetchall()
            for r in rows:
                vector = np.frombuffer(r["embedding"], dtype=np.float32)
                p_tag = r["pose_tag"] if "pose_tag" in r.keys() else "frontal"
                results.append((r["student_id"], r["student_number"], r["name"], vector, p_tag))
        return results

    def get_student_embeddings(self, student_id: int, model_name: Optional[str] = None) -> List[np.ndarray]:
        """Returns all embedding vectors stored for a given student, optionally filtered by model_name."""
        embeddings = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if model_name:
                cursor.execute(
                    "SELECT embedding FROM face_embeddings WHERE student_id = ? AND model_name = ?",
                    (student_id, model_name)
                )
            else:
                cursor.execute(
                    "SELECT embedding FROM face_embeddings WHERE student_id = ?",
                    (student_id,)
                )
            rows = cursor.fetchall()
            for r in rows:
                embeddings.append(np.frombuffer(r["embedding"], dtype=np.float32))
        return embeddings


class SessionRepository:
    def __init__(self, db_conn: DatabaseConnection):
        self.db = db_conn

    def create_session(self, session: AttendanceSession) -> AttendanceSession:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO attendance_sessions (date, subject, class_name, started_at, ended_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session.date, session.subject, session.class_name, session.started_at, session.ended_at)
            )
            session.id = cursor.lastrowid
            conn.commit()
        return session

    def end_session(self, session_id: int, ended_at: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE attendance_sessions SET ended_at = ? WHERE id = ?", (ended_at, session_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_by_id(self, session_id: int) -> Optional[AttendanceSession]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance_sessions WHERE id = ?", (session_id,))
            r = cursor.fetchone()
            if r:
                return AttendanceSession(
                    id=r["id"],
                    date=r["date"],
                    subject=r["subject"],
                    class_name=r["class_name"],
                    started_at=r["started_at"],
                    ended_at=r["ended_at"]
                )
        return None

    def list_sessions(self) -> List[AttendanceSession]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance_sessions ORDER BY id DESC")
            rows = cursor.fetchall()
            return [
                AttendanceSession(
                    id=r["id"],
                    date=r["date"],
                    subject=r["subject"],
                    class_name=r["class_name"],
                    started_at=r["started_at"],
                    ended_at=r["ended_at"]
                )
                for r in rows
            ]


class AttendanceRepository:
    def __init__(self, db_conn: DatabaseConnection):
        self.db = db_conn

    def record_attendance(self, attendance: Attendance) -> bool:
        """
        Record student attendance for session. Returns True if inserted, False if duplicate.
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                liveness_val = 1 if attendance.liveness_passed is True else (0 if attendance.liveness_passed is False else None)
                cursor.execute(
                    """
                    INSERT INTO attendance (session_id, student_id, marked_at, status, similarity, liveness_score, liveness_passed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (attendance.session_id, attendance.student_id, attendance.marked_at, attendance.status, attendance.similarity, attendance.liveness_score, liveness_val)
                )
                attendance.id = cursor.lastrowid
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Duplicate entry for session_id + student_id
            logger.info(f"Duplicate attendance ignored for student_id={attendance.student_id} in session_id={attendance.session_id}")
            return False

    def is_marked(self, session_id: int, student_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM attendance WHERE session_id = ? AND student_id = ?", (session_id, student_id))
            return cursor.fetchone() is not None

    def get_session_attendance(self, session_id: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.id, a.session_id, a.student_id, a.marked_at, a.status, a.similarity,
                       a.liveness_score, a.liveness_passed,
                       s.student_number, s.name, s.department, s.year
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.session_id = ?
                ORDER BY a.marked_at DESC
                """,
                (session_id,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_report_data(
        self,
        start_date: str = None,
        end_date: str = None,
        class_name: str = None,
        subject: str = None,
        department: str = None,
        year: str = None
    ) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT a.id, sess.date, sess.subject, sess.class_name,
                       s.student_number, s.name, s.department, s.year,
                       a.marked_at, a.status, a.similarity,
                       a.liveness_score, a.liveness_passed
                FROM attendance a
                JOIN attendance_sessions sess ON a.session_id = sess.id
                JOIN students s ON a.student_id = s.id
                WHERE 1=1
            """
            params = []
            if start_date:
                query += " AND sess.date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND sess.date <= ?"
                params.append(end_date)
            if class_name:
                query += " AND sess.class_name LIKE ?"
                params.append(f"%{class_name}%")
            if subject:
                query += " AND sess.subject LIKE ?"
                params.append(f"%{subject}%")
            if department and department != "All Departments":
                query += " AND s.department = ?"
                params.append(department)
            if year and year != "All Academic Years":
                query += " AND s.year = ?"
                params.append(year)

            query += " ORDER BY sess.date DESC, a.marked_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_recent_attendance(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve latest attendance records across sessions for live activity dashboard."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.id, a.session_id, a.student_id, a.marked_at, a.status, a.similarity,
                       a.liveness_score, a.liveness_passed,
                       s.student_number, s.name, s.department, s.year,
                       sess.class_name, sess.subject
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN attendance_sessions sess ON a.session_id = sess.id
                ORDER BY a.marked_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_records_by_ids(self, record_ids: List[int]) -> int:
        """Delete specific attendance records by their primary key IDs and clean up empty sessions."""
        if not record_ids:
            return 0
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in record_ids)
            cursor.execute(f"DELETE FROM attendance WHERE id IN ({placeholders})", record_ids)
            deleted = cursor.rowcount
            # Remove any sessions that have no attendance records remaining
            cursor.execute("""
                DELETE FROM attendance_sessions
                WHERE id NOT IN (SELECT DISTINCT session_id FROM attendance)
            """)
            conn.commit()
            return deleted

    def clear_all_attendance(self) -> int:
        """Delete all attendance records and sessions from the database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM attendance")
            row = cursor.fetchone()
            total = row["total"] if row else 0
            cursor.execute("DELETE FROM attendance")
            cursor.execute("DELETE FROM attendance_sessions")
            conn.commit()
            return total


class SecurityAuditRepository:
    def __init__(self, db_conn: DatabaseConnection):
        self.db = db_conn

    def log_audit(
        self,
        reason: str,
        matched_student_id: Optional[int] = None,
        matched_name: Optional[str] = None,
        liveness_score: float = 0.0,
        texture_score: float = 0.0,
        reflectance_score: float = 0.0,
        entropy_score: float = 0.0,
        motion_score: float = 0.0,
        snapshot_path: Optional[str] = None,
        ir_snapshot_path: Optional[str] = None
    ) -> int:
        """Log an intercepted spoof attempt with forensic snapshot paths."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO security_audits (
                    timestamp, matched_student_id, matched_name, reason,
                    liveness_score, texture_score, reflectance_score, entropy_score, motion_score,
                    snapshot_path, ir_snapshot_path
                )
                VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    matched_student_id, matched_name, reason,
                    liveness_score, texture_score, reflectance_score, entropy_score, motion_score,
                    snapshot_path, ir_snapshot_path
                )
            )
            audit_id = cursor.lastrowid
            conn.commit()
            return audit_id

    def get_all_audits(self, limit: int = 150) -> List[Dict[str, Any]]:
        """Retrieve recent security audit logs."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.*, s.student_number, s.department, s.year
                FROM security_audits a
                LEFT JOIN students s ON a.matched_student_id = s.id
                ORDER BY a.id DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def clear_audits(self) -> int:
        """Clear all forensic audit records."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM security_audits")
            row = cursor.fetchone()
            total = row["total"] if row else 0
            cursor.execute("DELETE FROM security_audits")
            conn.commit()
            return total




