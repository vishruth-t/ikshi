import json
import urllib.request
import urllib.error
import pytest
from database.connection import DatabaseConnection
from database.repositories import StudentRepository, SessionRepository, AttendanceRepository, FaceEmbeddingRepository
from attendance.session_manager import SessionManager
from mobile_companion.server import MobileCompanionServer, get_local_ip

@pytest.fixture
def companion_server(tmp_path):
    db_file = tmp_path / "test_comp.db"
    db = DatabaseConnection(str(db_file))
    student_repo = StudentRepository(db)
    session_repo = SessionRepository(db)
    attendance_repo = AttendanceRepository(db)
    session_mgr = SessionManager(session_repo, student_repo, attendance_repo)

    # Use port 5599 for test server to avoid conflicts
    server = MobileCompanionServer(session_mgr, attendance_repo, student_repo, port=5599)
    success = server.start()
    assert success is True

    yield server, session_mgr, student_repo

    server.stop()

def test_mobile_server_html_and_status_endpoints(companion_server):
    server, session_mgr, student_repo = companion_server
    base_url = "http://127.0.0.1:5599"

    # Test GET /
    with urllib.request.urlopen(f"{base_url}/") as response:
        assert response.status == 200
        html = response.read().decode("utf-8")
        assert "FaceAttend Mobile" in html

    # Test GET /api/status (Inactive initially)
    with urllib.request.urlopen(f"{base_url}/api/status") as response:
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        assert data["session_active"] is False
        assert data["present_count"] == 0

def test_mobile_server_session_lifecycle(companion_server):
    server, session_mgr, student_repo = companion_server
    base_url = "http://127.0.0.1:5599"

    # 1. Start Session via Mobile POST
    start_payload = json.dumps({"class_name": "CS-501", "subject": "Deep Vision"}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/session/start",
        data=start_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        res_data = json.loads(response.read().decode("utf-8"))
        assert res_data["success"] is True

    # 2. Check /api/status
    with urllib.request.urlopen(f"{base_url}/api/status") as response:
        data = json.loads(response.read().decode("utf-8"))
        assert data["session_active"] is True
        assert data["class_name"] == "CS-501"
        assert data["subject"] == "Deep Vision"

    # 3. Stop Session via Mobile POST
    req_stop = urllib.request.Request(
        f"{base_url}/api/session/stop",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_stop) as response:
        assert response.status == 200
        res_data = json.loads(response.read().decode("utf-8"))
        assert res_data["success"] is True

    # 4. Verify status is Standby
    with urllib.request.urlopen(f"{base_url}/api/status") as response:
        data = json.loads(response.read().decode("utf-8"))
        assert data["session_active"] is False
