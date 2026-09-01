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
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO face_embeddings (student_id, embedding, model_name, model_version, metric, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (embedding.student_id, blob_data, embedding.model_name, embedding.model_version, embedding.metric, embedding.created_at)
            )
            embedding.id = cursor.lastrowid
            conn.commit()
        return embedding

    def delete_embeddings_for_student(self, student_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM face_embeddings WHERE student_id = ?", (student_id,))
            conn.commit()

    def get_all_embeddings(self) -> List[Tuple[int, str, str, np.ndarray]]:
        """
        Returns list of (student_id, student_number, student_name, embedding_vector)
        for all active students.
        """
        results = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.student_id, s.student_number, s.name, e.embedding
                FROM face_embeddings e
                JOIN students s ON e.student_id = s.id
                WHERE s.active = 1
                """
            )
            rows = cursor.fetchall()
            for r in rows:
                vector = np.frombuffer(r["embedding"], dtype=np.float32)
                results.append((r["student_id"], r["student_number"], r["name"], vector))
        return results


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
                cursor.execute(
                    """
                    INSERT INTO attendance (session_id, student_id, marked_at, status, similarity)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (attendance.session_id, attendance.student_id, attendance.marked_at, attendance.status, attendance.similarity)
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
                       a.marked_at, a.status, a.similarity
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

