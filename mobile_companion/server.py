import json
import socket
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Optional

from mobile_companion.web_template import MOBILE_HTML_TEMPLATE
from attendance.session_manager import SessionManager
from database.repositories import AttendanceRepository, StudentRepository

logger = logging.getLogger(__name__)

def get_local_ip() -> str:
    """Retrieve local LAN IP address of this computer."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class MobileCompanionHandler(BaseHTTPRequestHandler):
    session_manager: SessionManager = None
    attendance_repo: AttendanceRepository = None
    student_repo: StudentRepository = None

    def log_message(self, format, *args):
        # Suppress noisy standard HTTP access logs
        return

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ["/", "/index.html"]:
            html = MOBILE_HTML_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if path == "/api/status":
            stats = self.session_manager.get_session_stats()
            total_students = len(self.student_repo.get_all(active_only=True))
            data = {
                "session_active": stats.get("active", False),
                "session_id": stats.get("session_id"),
                "class_name": stats.get("class_name", ""),
                "subject": stats.get("subject", ""),
                "present_count": stats.get("present_count", 0),
                "total_enrolled": total_students,
                "attendance_percentage": stats.get("attendance_percentage", 0.0)
            }
            self._send_json(data)
            return

        if path == "/api/live-roll":
            active_sess = self.session_manager.get_active_session()
            if active_sess and active_sess.id:
                records = self.attendance_repo.get_session_attendance(active_sess.id)
                self._send_json(records)
            else:
                self._send_json([])
            return

        if path == "/api/students":
            students = self.student_repo.get_all(active_only=True)
            data = [{"id": s.id, "name": s.name, "student_number": s.student_number, "department": s.department} for s in students]
            self._send_json(data)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/session/start":
            cls = payload.get("class_name", "CS-101")
            subj = payload.get("subject", "General Attendance")
            self.session_manager.start_session(subj, cls)
            self._send_json({"success": True, "message": f"Started session for {cls} - {subj}"})
            return

        if path == "/api/session/stop":
            self.session_manager.end_session()
            self._send_json({"success": True, "message": "Session ended"})
            return

        self.send_error(404, "Endpoint not found")


class MobileCompanionServer:
    def __init__(
        self,
        session_manager: SessionManager,
        attendance_repo: AttendanceRepository,
        student_repo: StudentRepository,
        port: int = 5555
    ):
        self.port = port
        self.server: Optional[ThreadedHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False

        # Set class-level dependencies on handler
        MobileCompanionHandler.session_manager = session_manager
        MobileCompanionHandler.attendance_repo = attendance_repo
        MobileCompanionHandler.student_repo = student_repo

    def start(self) -> bool:
        if self.is_running:
            return True
        try:
            self.server = ThreadedHTTPServer(("0.0.0.0", self.port), MobileCompanionHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            self.is_running = True
            logger.info(f"Mobile Companion Web Server started at http://{get_local_ip()}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start Mobile Companion Server on port {self.port}: {e}")
            return False

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        self.is_running = False
        logger.info("Mobile Companion Web Server stopped.")

    def get_url(self) -> str:
        return f"http://{get_local_ip()}:{self.port}"
