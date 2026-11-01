"""Stage 8 tests: FastAPI integration tests with TestClient.

Every endpoint, success path, and error code mapping is verified.
All tests run in an isolated temporary environment.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import jdatetime
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import attendance_service, config, database, recognition
from backend.api.app import app
from backend.utils import now_tehran, parse_iso


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate DB, folders, and streak trackers, and provide a TestClient."""
    db_path = tmp_path / "stage8_test.db"
    known_faces = tmp_path / "known_faces"
    embeddings = tmp_path / "embeddings"
    reports = tmp_path / "reports"
    known_faces.mkdir(parents=True, exist_ok=True)
    embeddings.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("ATTENDANCE_DB", str(db_path))
    monkeypatch.setattr(config, "KNOWN_FACES_DIR", known_faces)
    monkeypatch.setattr(config, "EMBEDDINGS_DIR", embeddings)
    monkeypatch.setattr(config, "REPORTS_DIR", reports)

    database.init_db()
    attendance_service.streak_trackers.clear()

    with TestClient(app) as test_client:
        yield test_client

    attendance_service.streak_trackers.clear()


# --------------------------------------------------------------------------- #
# Health Check
# --------------------------------------------------------------------------- #
def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --------------------------------------------------------------------------- #
# Students CRUD & Errors
# --------------------------------------------------------------------------- #
def test_students_crud(client: TestClient):
    # Initial list is empty
    resp = client.get("/students")
    assert resp.status_code == 200
    assert resp.json() == []

    # Create student
    payload = {
        "student_id": "std_101",
        "full_name": "علی رضایی",
        "major": "مهندسی کامپیوتر",
        "term": "مهر 1405",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_id"] == "std_101"
    assert data["full_name"] == "علی رضایی"
    assert data["photo_count"] == 0
    assert data["has_embedding"] is False

    # List now contains the student
    resp = client.get("/students")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["student_id"] == "std_101"

    # Duplicate student returns 409
    resp = client.post("/students", json=payload)
    assert resp.status_code == 409
    err = resp.json()
    assert err["error"] == "student_exists"
    assert "قبلاً ثبت شده" in err["message"]

    # Invalid input (empty name) returns 422
    resp = client.post("/students", json={"student_id": "std_102", "full_name": ""})
    assert resp.status_code == 422
    assert resp.json()["error"] == "invalid_input"

    # Update student
    resp = client.put(
        "/students/std_101",
        json={"full_name": "علی رضایی‌اصل", "term": "بهمن 1405"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "علی رضایی‌اصل"
    assert data["term"] == "بهمن 1405"
    assert data["major"] == "مهندسی کامپیوتر"

    # Update non-existent student returns 404
    resp = client.put("/students/std_999", json={"full_name": "ناشناس"})
    assert resp.status_code == 404
    assert resp.json()["error"] == "student_not_found"

    # Delete non-existent student returns 404
    resp = client.delete("/students/std_999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "student_not_found"

    # Delete student
    resp = client.delete("/students/std_101")
    assert resp.status_code == 200
    assert resp.json() == {"success": True, "student_id": "std_101"}

    # List is empty again
    resp = client.get("/students")
    assert resp.json() == []


def test_student_persian_digit_normalization(client: TestClient):
    payload = {
        "student_id": "۹۹۱۲۳۴۵",
        "full_name": "سارا محمدی",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 200
    assert resp.json()["student_id"] == "9912345"

    # Query with English or Persian digit works
    resp = client.put("/students/۹۹۱۲۳۴۵", json={"major": "هوش مصنوعی"})
    assert resp.status_code == 200
    assert resp.json()["major"] == "هوش مصنوعی"

    resp = client.delete("/students/9912345")
    assert resp.status_code == 200


def test_process_photos_endpoint(client: TestClient):
    # Non-existent student
    resp = client.post("/students/unknown_std/process-photos")
    assert resp.status_code == 404
    assert resp.json()["error"] == "student_not_found"

    # Student with no photos -> 422 not_enough_photos
    client.post("/students", json={"student_id": "std_empty", "full_name": "بدون عکس"})
    resp = client.post("/students/std_empty/process-photos")
    assert resp.status_code == 422
    assert resp.json()["error"] == "not_enough_photos"


# --------------------------------------------------------------------------- #
# Courses Endpoint
# --------------------------------------------------------------------------- #
def test_get_courses(client: TestClient):
    resp = client.get("/courses")
    assert resp.status_code == 200
    courses = resp.json()
    assert isinstance(courses, list)
    assert len(courses) >= 1
    assert courses[0]["id"] == 1
    assert courses[0]["title"] == "کلاس اصلی"


# --------------------------------------------------------------------------- #
# Sessions Lifecycle & Errors
# --------------------------------------------------------------------------- #
def test_sessions_lifecycle(client: TestClient):
    # Initially no active session
    resp = client.get("/sessions/active")
    assert resp.status_code == 200
    assert resp.json() is None

    # Closing when no session is active returns 409
    resp = client.post("/sessions/close")
    assert resp.status_code == 409
    assert resp.json()["error"] == "no_active_session"

    # Start a session
    resp = client.post("/sessions/start", json={"course_id": 1, "late_after_minutes": 15})
    assert resp.status_code == 200
    session = resp.json()
    assert session["course_id"] == 1
    assert session["late_after_minutes"] == 15
    assert session["status"] == "active"
    session_id = session["id"]

    # Active session is returned
    resp = client.get("/sessions/active")
    assert resp.status_code == 200
    assert resp.json()["id"] == session_id

    # Trying to start a second session returns 409
    resp = client.post("/sessions/start", json={"course_id": 1})
    assert resp.status_code == 409
    assert resp.json()["error"] == "session_already_active"

    # List sessions
    resp = client.get("/sessions?limit=10")
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id

    # Invalid limit returns 422
    resp = client.get("/sessions?limit=1000")
    assert resp.status_code == 422
    assert resp.json()["error"] == "invalid_input"

    # Close the session
    resp = client.post("/sessions/close")
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"
    assert resp.json()["ended_at"] is not None

    # No active session anymore
    resp = client.get("/sessions/active")
    assert resp.status_code == 200
    assert resp.json() is None

    # Close non-existent session by id returns 404
    resp = client.post("/sessions/close", json={"session_id": 9999})
    assert resp.status_code == 404
    assert resp.json()["error"] == "session_not_found"


# --------------------------------------------------------------------------- #
# Manual Attendance & Constraints
# --------------------------------------------------------------------------- #
def test_manual_attendance_and_delete_protection(client: TestClient):
    # Create student
    client.post("/students", json={"student_id": "std_att", "full_name": "محمد علوی"})

    # Start session
    session_resp = client.post("/sessions/start", json={"course_id": 1})
    session_id = session_resp.json()["id"]

    # Manual attendance log
    resp = client.put(f"/sessions/{session_id}/attendance/std_att")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Duplicate manual log -> returns success=False with reason="already_present"
    dup_resp = client.put(f"/sessions/{session_id}/attendance/std_att")
    assert dup_resp.status_code == 200
    assert dup_resp.json()["success"] is False
    assert dup_resp.json()["reason"] == "already_present"

    # Attendance query returns student as present
    resp = client.get(f"/sessions/{session_id}/attendance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["present"] == 1
    assert data["summary"]["absent"] == 0
    records = data["attendance"]
    assert len(records) == 1
    assert records[0]["student_id"] == "std_att"
    assert records[0]["status"] == "present"
    assert records[0]["source"] == "manual"
    # Ensure redundant keys students/records are not present in response
    assert "students" not in data or data["students"] is None
    assert "records" not in data or data["records"] is None

    # Trying to delete student without force returns 409
    resp = client.delete("/students/std_att?force=false")
    assert resp.status_code == 409
    assert resp.json()["error"] == "student_has_attendance"

    # Remove attendance
    resp = client.delete(f"/sessions/{session_id}/attendance/std_att")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Attendance query now shows student as absent
    resp = client.get(f"/sessions/{session_id}/attendance")
    assert resp.json()["summary"]["absent"] == 1
    assert resp.json()["summary"]["present"] == 0

    # Delete student now succeeds without force
    resp = client.delete("/students/std_att")
    assert resp.status_code == 200

    # Close session
    client.post("/sessions/close")

    # Logging attendance on closed session returns 409
    resp = client.put(f"/sessions/{session_id}/attendance/std_att")
    assert resp.status_code == 409
    assert resp.json()["error"] == "no_active_session"

    # Removing attendance on closed session returns 409
    resp = client.delete(f"/sessions/{session_id}/attendance/std_att")
    assert resp.status_code == 409
    assert resp.json()["error"] == "no_active_session"


def test_attendance_nonexistent_session(client: TestClient):
    resp = client.get("/sessions/9999/attendance")
    assert resp.status_code == 404
    assert resp.json()["error"] == "session_not_found"


# --------------------------------------------------------------------------- #
# Recognize Endpoint (Camera / Video Frames)
# --------------------------------------------------------------------------- #
def test_recognize_endpoint_flow(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    # Setup student
    client.post("/students", json={"student_id": "std_rec", "full_name": "مریم احمدی"})

    # Start session
    session_resp = client.post("/sessions/start", json={"course_id": 1})
    session_id = session_resp.json()["id"]

    # Prepare a valid 100x100 jpeg image
    frame_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", frame_bgr)
    image_bytes = encoded.tobytes()

    # Case 0: File exceeds 10MB limit returns 413
    oversized = b"x" * (10 * 1024 * 1024 + 100)
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("large.jpg", oversized, "image/jpeg")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"] == "payload_too_large"
    assert "بیش از حد مجاز" in resp.json()["message"]

    # Case 0b: Empty file returns 422
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "invalid_input"

    # Case 1: Corrupted or non-image file returns 422
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "invalid_input"

    # Case 2: Blank image with no faces detected
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recorded"] == []
    assert data["already_present"] == []
    assert data["faces"] == []

    # Case 3: Mock face recognition detection across 3 consecutive frames
    simulated_match = [
        {
            "student_id": "std_rec",
            "distance": 0.35,
            "box": (0.1, 0.8, 0.7, 0.2),
        }
    ]
    monkeypatch.setattr(recognition, "recognize_frame", lambda bgr: simulated_match)

    # Frame 1: streak = 1
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["pending"]["std_rec"] == 1
    assert resp.json()["recorded"] == []
    assert len(resp.json()["faces"]) == 1
    assert resp.json()["faces"][0]["student_id"] == "std_rec"

    # Frame 2: streak = 2
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["pending"]["std_rec"] == 2
    assert resp.json()["recorded"] == []

    # Frame 3: threshold reached (3 frames) -> recorded!
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["recorded"] == ["std_rec"]
    assert "std_rec" not in resp.json()["pending"]

    # Frame 4: student already present
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["already_present"] == ["std_rec"]

    # Close session
    client.post("/sessions/close")

    # Calling recognize on closed session returns 409
    resp = client.post(
        f"/sessions/{session_id}/recognize",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "no_active_session"


def test_recognize_nonexistent_session(client: TestClient):
    frame_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", frame_bgr)
    image_bytes = encoded.tobytes()

    resp = client.post(
        "/sessions/9999/recognize",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "session_not_found"


# --------------------------------------------------------------------------- #
# Report Downloads & Errors
# --------------------------------------------------------------------------- #
def test_session_report_download(client: TestClient):
    # Start and close session with a student
    client.post("/students", json={"student_id": "std_rep", "full_name": "نرگس کریمی"})
    session_resp = client.post("/sessions/start", json={"course_id": 1})
    session_id = session_resp.json()["id"]
    client.put(f"/sessions/{session_id}/attendance/std_rep")
    client.post("/sessions/close")

    # Download session report
    resp = client.get(f"/sessions/{session_id}/report")
    assert resp.status_code == 200
    assert "spreadsheetml.sheet" in resp.headers["content-type"]
    assert len(resp.content) > 1000

    # Non-existent session report returns 404
    resp = client.get("/sessions/9999/report")
    assert resp.status_code == 404
    assert resp.json()["error"] == "session_not_found"


def test_daily_report_download(client: TestClient):
    # Start and close session today
    session_resp = client.post("/sessions/start", json={"course_id": 1})
    started_at = session_resp.json()["started_at"]
    client.post("/sessions/close")

    # Calculate Jalali date
    dt = parse_iso(started_at)
    jalali = jdatetime.datetime.fromgregorian(datetime=dt)
    jalali_date = f"{jalali.year:04d}-{jalali.month:02d}-{jalali.day:02d}"

    # Download daily report
    resp = client.get(f"/reports/daily?date={jalali_date}")
    assert resp.status_code == 200
    assert "spreadsheetml.sheet" in resp.headers["content-type"]
    assert len(resp.content) > 1000

    # Date with no sessions returns 404 report_empty
    resp = client.get("/reports/daily?date=1399-01-01")
    assert resp.status_code == 404
    assert resp.json()["error"] == "report_empty"

    # Malformed date returns 422
    resp = client.get("/reports/daily?date=invalid-date")
    assert resp.status_code == 422
    assert resp.json()["error"] == "invalid_input"


# --------------------------------------------------------------------------- #
# CORS Headers
# --------------------------------------------------------------------------- #
def test_cors_headers(client: TestClient):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    resp = client.options("/health", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


# --------------------------------------------------------------------------- #
# Extra Edge Cases & Error Mappings
# --------------------------------------------------------------------------- #
def test_session_start_default_body(client: TestClient):
    # Start session with no body provided
    resp = client.post("/sessions/start")
    assert resp.status_code == 200
    assert resp.json()["course_id"] == 1
    assert resp.json()["status"] == "active"
    client.post("/sessions/close")


def test_session_close_by_id(client: TestClient):
    # Test closing active session with empty body {}
    client.post("/sessions/start")
    resp_close_empty = client.post("/sessions/close", json={})
    assert resp_close_empty.status_code == 200
    assert resp_close_empty.json()["status"] == "closed"

    resp = client.post("/sessions/start")
    session_id = resp.json()["id"]

    # Close explicitly by session_id in body
    resp = client.post("/sessions/close", json={"session_id": session_id})
    assert resp.status_code == 200
    assert resp.json()["id"] == session_id
    assert resp.json()["status"] == "closed"

    # Closing already closed session returns 409 session_closed
    resp = client.post("/sessions/close", json={"session_id": session_id})
    assert resp.status_code == 409
    assert resp.json()["error"] == "session_closed"


def test_student_force_delete_with_attendance(client: TestClient):
    client.post("/students", json={"student_id": "std_force", "full_name": "سعید رضایی"})
    session_resp = client.post("/sessions/start")
    session_id = session_resp.json()["id"]

    # Log attendance
    client.put(f"/sessions/{session_id}/attendance/std_force")

    # Delete with force=true
    resp = client.delete("/students/std_force?force=true")
    assert resp.status_code == 200
    assert resp.json() == {"success": True, "student_id": "std_force"}

    # Verify student is deleted
    assert client.get("/students").json() == []
    client.post("/sessions/close")


def test_attendance_persian_digits_in_url(client: TestClient):
    client.post("/students", json={"student_id": "998877", "full_name": "زهرا حسینی"})
    session_resp = client.post("/sessions/start")
    session_id = session_resp.json()["id"]

    # Put with Persian digits
    resp = client.put(f"/sessions/{session_id}/attendance/۹۹۸۸۷۷")
    assert resp.status_code == 200
    assert resp.json()["student_id"] == "998877"

    # Delete with Persian digits
    resp = client.delete(f"/sessions/{session_id}/attendance/۹۹۸۸۷۷")
    assert resp.status_code == 200
    assert resp.json()["student_id"] == "998877"

    client.post("/sessions/close")

