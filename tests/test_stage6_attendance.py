"""Stage 6 tests: attendance_service.py.

All tests use a temporary database via the ATTENDANCE_DB environment variable.
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest

from backend import attendance_service, database, session_manager
from backend.errors import InvalidInputError, NoActiveSessionError, SessionNotFoundError
from backend.utils import now_tehran, to_iso


@pytest.fixture(autouse=True)
def temp_db_and_tracker(tmp_path, monkeypatch):
    """Isolate the database and clear streak trackers before each test."""
    db_path = tmp_path / "stage6_test.db"
    monkeypatch.setenv("ATTENDANCE_DB", str(db_path))
    database.init_db()
    
    # Clear streak trackers before each test to prevent leakage
    attendance_service.streak_trackers.clear()
    
    yield db_path


def _create_student(student_id: str, full_name: str = "Test Student"):
    connection = database.get_connection()
    try:
        connection.execute(
            "INSERT INTO students (student_id, full_name, major, term, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (student_id, full_name, "Test Major", "Test Term", to_iso(now_tehran())),
        )
        connection.commit()
    finally:
        connection.close()


def test_log_attendance_new_and_duplicate(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S001")
    
    assert attendance_service.log_attendance(session["id"], "S001", source="face", confidence=0.5) is True
    assert attendance_service.log_attendance(session["id"], "S001", source="face", confidence=0.5) is False


def test_log_attendance_requires_active_session(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S001")
    session_manager.close_session(session["id"])
    
    with pytest.raises(NoActiveSessionError):
        attendance_service.log_attendance(session["id"], "S001", source="face")
    with pytest.raises(NoActiveSessionError):
        attendance_service.log_attendance(session["id"], "S001", source="manual")


def test_remove_attendance(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S001")
    attendance_service.log_attendance(session["id"], "S001", source="manual")
    
    assert attendance_service.remove_attendance(session["id"], "S001") is True
    assert attendance_service.remove_attendance(session["id"], "S001") is False
    
    session_manager.close_session(session["id"])
    with pytest.raises(NoActiveSessionError):
        attendance_service.remove_attendance(session["id"], "S001")


def test_get_session_attendance_and_summary(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S001", "Present Student")
    _create_student("S002", "Late Student")
    _create_student("S003", "Absent Student")
    
    attendance_service.log_attendance(session["id"], "S001", source="face")
    
    late_time = to_iso(now_tehran() + timedelta(minutes=15))
    connection = database.get_connection()
    try:
        connection.execute(
            "INSERT INTO attendance (session_id, student_id, checked_at, source) VALUES (?, ?, ?, ?)",
            (session["id"], "S002", late_time, "manual")
        )
        connection.commit()
    finally:
        connection.close()
    
    attendance_list = attendance_service.get_session_attendance(session["id"])
    assert len(attendance_list) == 3
    
    assert next(a for a in attendance_list if a["student_id"] == "S001")["status"] == "present"
    assert next(a for a in attendance_list if a["student_id"] == "S002")["status"] == "late"
    assert next(a for a in attendance_list if a["student_id"] == "S003")["status"] == "absent"
    
    summary = attendance_service.get_session_summary(session["id"])
    assert summary == {"total": 3, "present": 1, "late": 1, "absent": 1}


def test_process_recognition_result_streak_logic(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S001")
    
    # Frame 1 & 2: pending
    attendance_service.process_recognition_result(session["id"], [{"student_id": "S001", "distance": 0.4}])
    attendance_service.process_recognition_result(session["id"], [{"student_id": "S001", "distance": 0.4}])
    assert attendance_service.streak_trackers[session["id"]]["S001"] == 2
    
    # Frame 3: recorded
    result = attendance_service.process_recognition_result(session["id"], [{"student_id": "S001", "distance": 0.4}])
    assert result["recorded"] == ["S001"]
    assert result["pending"] == {}
    
    # Frame 4: already present
    result4 = attendance_service.process_recognition_result(session["id"], [{"student_id": "S001", "distance": 0.4}])
    assert result4["already_present"] == ["S001"]
    
    # Frame 5: unknown face
    result5 = attendance_service.process_recognition_result(session["id"], [{"student_id": None, "distance": 0.8}])
    assert result5["unknown_count"] == 1


def test_process_recognition_result_streak_reset(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S001")
    
    attendance_service.process_recognition_result(session["id"], [{"student_id": "S001", "distance": 0.4}])
    assert attendance_service.streak_trackers[session["id"]]["S001"] == 1
    
    attendance_service.process_recognition_result(session["id"], [])
    assert "S001" not in attendance_service.streak_trackers[session["id"]]


def test_exact_boundary_present(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S_ON_TIME")
    _create_student("S_LATE")
    
    from backend.utils import parse_iso
    started = parse_iso(session["started_at"])
    
    # Exact boundary: checked_at == started + 10 minutes -> must be PRESENT
    exact_time = to_iso(started + timedelta(minutes=10))
    # 1 second after boundary -> must be LATE
    late_time = to_iso(started + timedelta(minutes=10, seconds=1))
    
    connection = database.get_connection()
    try:
        connection.execute(
            "INSERT INTO attendance (session_id, student_id, checked_at, source) VALUES (?, ?, ?, 'manual')",
            (session["id"], "S_ON_TIME", exact_time),
        )
        connection.execute(
            "INSERT INTO attendance (session_id, student_id, checked_at, source) VALUES (?, ?, ?, 'manual')",
            (session["id"], "S_LATE", late_time),
        )
        connection.commit()
    finally:
        connection.close()
        
    records = attendance_service.get_session_attendance(session["id"])
    rec_on_time = next(r for r in records if r["student_id"] == "S_ON_TIME")
    rec_late = next(r for r in records if r["student_id"] == "S_LATE")
    assert rec_on_time["status"] == "present"
    assert rec_late["status"] == "late"


def test_streak_gap_reset_scenario(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S_GAP")
    
    # Frame 1: seen
    res1 = attendance_service.process_recognition_result(session["id"], [{"student_id": "S_GAP", "distance": 0.4}])
    assert res1["pending"]["S_GAP"] == 1
    assert res1["recorded"] == []
    
    # Frame 2: seen
    res2 = attendance_service.process_recognition_result(session["id"], [{"student_id": "S_GAP", "distance": 0.4}])
    assert res2["pending"]["S_GAP"] == 2
    assert res2["recorded"] == []
    
    # Frame 3: absent -> streak reset/deleted
    res3 = attendance_service.process_recognition_result(session["id"], [])
    assert "S_GAP" not in res3["pending"]
    assert res3["recorded"] == []
    
    # Frame 4: seen again -> starts at 1, not 3!
    res4 = attendance_service.process_recognition_result(session["id"], [{"student_id": "S_GAP", "distance": 0.4}])
    assert res4["pending"]["S_GAP"] == 1
    assert res4["recorded"] == []
    
    # Frame 5: seen again -> 2
    res5 = attendance_service.process_recognition_result(session["id"], [{"student_id": "S_GAP", "distance": 0.4}])
    assert res5["pending"]["S_GAP"] == 2
    assert res5["recorded"] == []


def test_unknown_face_logging(temp_db_and_tracker, caplog):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    
    with caplog.at_level("INFO"):
        res = attendance_service.process_recognition_result(
            session["id"], [{"student_id": None, "distance": 0.75}]
        )
    assert res["unknown_count"] == 1
    assert any("چهره ناشناس دیده شد" in record.message for record in caplog.records)


def test_concurrent_multithreaded_streak(temp_db_and_tracker):
    from concurrent.futures import ThreadPoolExecutor
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S_CONCURRENT")
    
    results = []
    def worker():
        res = attendance_service.process_recognition_result(
            session["id"], [{"student_id": "S_CONCURRENT", "distance": 0.3}]
        )
        results.append(res)
        
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker) for _ in range(10)]
        for f in futures:
            f.result()
            
    attendance = attendance_service.get_session_attendance(session["id"])
    assert len(attendance) == 1
    assert attendance[0]["status"] == "present"
    recorded_total = sum(len(r["recorded"]) for r in results)
    assert recorded_total == 1



def test_streak_trackers_cleared_after_close_session(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    _create_student("S001")
    
    attendance_service.process_recognition_result(session["id"], [{"student_id": "S001", "distance": 0.4}])
    assert session["id"] in attendance_service.streak_trackers
    
    session_manager.close_session(session["id"])
    assert session["id"] not in attendance_service.streak_trackers


def test_log_attendance_for_nonexistent_student(temp_db_and_tracker):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    
    with pytest.raises(InvalidInputError):
        attendance_service.log_attendance(session["id"], "NONEXISTENT", source="manual")