import sqlite3
import os
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Students table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                year TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # Face embeddings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                metric TEXT NOT NULL,
                pose_tag TEXT DEFAULT 'frontal',
                created_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            """)

            try:
                cursor.execute("ALTER TABLE face_embeddings ADD COLUMN pose_tag TEXT DEFAULT 'frontal';")
            except Exception:
                pass

            # Attendance sessions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                subject TEXT NOT NULL,
                class_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT
            );
            """)

            # Attendance records table with UNIQUE constraint and optional IR liveness audit fields
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                marked_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Present',
                similarity REAL NOT NULL,
                liveness_score REAL,
                liveness_passed INTEGER,
                UNIQUE(session_id, student_id),
                FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            """)

            # Security Audits & Spoof Interceptions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                matched_student_id INTEGER,
                matched_name TEXT,
                reason TEXT NOT NULL,
                liveness_score REAL,
                texture_score REAL,
                reflectance_score REAL,
                entropy_score REAL,
                motion_score REAL,
                snapshot_path TEXT,
                ir_snapshot_path TEXT,
                FOREIGN KEY (matched_student_id) REFERENCES students(id) ON DELETE SET NULL
            );
            """)

            # Schema migration: check and dynamically add liveness columns if table was created in earlier version
            cursor.execute("PRAGMA table_info(attendance);")
            existing_cols = {row["name"] for row in cursor.fetchall()}
            if "liveness_score" not in existing_cols:
                cursor.execute("ALTER TABLE attendance ADD COLUMN liveness_score REAL;")
            if "liveness_passed" not in existing_cols:
                cursor.execute("ALTER TABLE attendance ADD COLUMN liveness_passed INTEGER;")

            # Performance Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON attendance(student_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_session_id ON attendance(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_marked_at ON attendance(marked_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_date ON attendance_sessions(date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_number ON students(student_number);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_audits_time ON security_audits(timestamp);")

            conn.commit()
            logger.info("Database initialized successfully with schemas and indexes.")
