"""Stage 9 tests: manage.py and main_test.py.

All tests execute non-interactively using temporary databases and mock camera/GUI
facilities so no real hardware, live servers, or persistent databases are touched.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock

import jdatetime
import numpy as np
import pytest

import main_test
import manage
from backend import attendance_service, config, database, enrollment, session_manager
from backend.utils import now_tehran, to_iso


@pytest.fixture(autouse=True)
def temp_environment(tmp_path, monkeypatch):
    """Isolate DB, reports, embeddings, and known_faces in tmp_path."""
    db_path = tmp_path / "stage9_test.db"
    monkeypatch.setenv("ATTENDANCE_DB", str(db_path))

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "REPORTS_DIR", reports_dir)

    known_faces_dir = tmp_path / "known_faces"
    known_faces_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "KNOWN_FACES_DIR", known_faces_dir)

    embeddings_dir = tmp_path / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "EMBEDDINGS_DIR", embeddings_dir)

    attendance_service.streak_trackers.clear()
    database.init_db()

    yield {
        "db": db_path,
        "reports": reports_dir,
        "known_faces": known_faces_dir,
        "embeddings": embeddings_dir,
    }


# =========================================================================== #
# manage.py tests
# =========================================================================== #


def assert_no_persian(text: str):
    """Verify that text does not contain any Persian or non-ASCII characters."""
    non_ascii = [c for c in text if ord(c) >= 128]
    assert not non_ascii, f"Found non-ASCII characters in English output: {set(non_ascii)}"


def test_manage_init_db(capsys):
    # Default en
    ret = manage.main(["init-db"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- Database Initialized" in captured.out
    assert "Success" in captured.out
    assert "Next step" in captured.out
    assert_no_persian(captured.out)

    # fa flag
    ret_fa = manage.main(["--lang", "fa", "init-db"])
    assert ret_fa == 0
    captured_fa = capsys.readouterr()
    assert "+-- مقداردهی اولیه پایگاه داده" in captured_fa.out
    assert "موفقیت‌آمیز" in captured_fa.out
    assert "Warning: Windows PowerShell console" in captured_fa.err


def test_manage_add_student_success_and_duplicate(capsys):
    # 1. Add student successfully (en)
    ret = manage.main(["add-student", "--id", "S1001", "--name", "علی رضایی", "--major", "مهندسی کامپیوتر", "--term", "4"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- Student Registered" in captured.out
    assert "S1001" in captured.out
    assert "(Persian name)" in captured.out
    assert "(Persian)" in captured.out
    assert "Next step" in captured.out
    assert_no_persian(captured.out)

    # Verify student exists in DB with original Persian name
    student = enrollment.get_student("S1001")
    assert student is not None
    assert student["full_name"] == "علی رضایی"

    # 2. Add student with fa flag
    ret_fa = manage.main(["--lang", "fa", "add-student", "--id", "S1002", "--name", "سارا احمدی", "--major", "برق", "--term", "2"])
    assert ret_fa == 0
    captured_fa = capsys.readouterr()
    assert "+-- ثبت دانشجو" in captured_fa.out
    assert "S1002" in captured_fa.out
    assert "Warning: Windows PowerShell console" in captured_fa.err

    # 3. Add same student again -> Duplicate error (en)
    ret_dup = manage.main(["add-student", "--id", "S1001", "--name", "علی رضایی"])
    assert ret_dup == 1
    captured_dup = capsys.readouterr()
    assert "Error [student_exists]" in captured_dup.err
    assert_no_persian(captured_dup.err)

    # 4. Duplicate error (fa)
    ret_dup_fa = manage.main(["--lang", "fa", "add-student", "--id", "S1001", "--name", "علی رضایی"])
    assert ret_dup_fa == 1
    captured_dup_fa = capsys.readouterr()
    assert "خطا [student_exists]" in captured_dup_fa.err


def test_manage_add_student_invalid_inputs(capsys):
    ret = manage.main(["add-student", "--id", "", "--name", ""])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error [invalid_input]" in captured.err
    assert_no_persian(captured.err)


def test_manage_delete_student(capsys):
    # 1. Add student
    manage.main(["add-student", "--id", "S2001", "--name", "مریم حسینی"])
    assert enrollment.get_student("S2001") is not None

    # 2. Delete student without force (en)
    ret = manage.main(["delete-student", "--id", "S2001"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- Student Deleted" in captured.out
    assert "S2001" in captured.out
    assert "Force" in captured.out
    assert "False" in captured.out
    assert "Next step" in captured.out
    assert_no_persian(captured.out)
    assert enrollment.get_student("S2001") is None

    # 3. Delete nonexistent student
    ret_nonexistent = manage.main(["delete-student", "--id", "99999"])
    assert ret_nonexistent == 1
    captured_nonexistent = capsys.readouterr()
    assert "Error [student_not_found]" in captured_nonexistent.err
    assert_no_persian(captured_nonexistent.err)

    # 4. Delete student with attendance protection
    manage.main(["add-student", "--id", "S2002", "--name", "رضا راد"])
    session = session_manager.start_session(course_id=1)
    attendance_service.log_attendance(session["id"], "S2002", source="manual")

    # Attempt delete without force -> Blocked
    ret_blocked = manage.main(["delete-student", "--id", "S2002"])
    assert ret_blocked == 1
    captured_blocked = capsys.readouterr()
    assert "Error [student_has_attendance]" in captured_blocked.err
    assert_no_persian(captured_blocked.err)

    # Delete with --force -> Success
    ret_force = manage.main(["delete-student", "--id", "S2002", "--force"])
    assert ret_force == 0
    captured_force = capsys.readouterr()
    assert "+-- Student Deleted" in captured_force.out
    assert "Force" in captured_force.out
    assert "True" in captured_force.out
    assert_no_persian(captured_force.out)
    assert enrollment.get_student("S2002") is None


def test_manage_process_photos_not_found(capsys):
    ret = manage.main(["process-photos", "--id", "NONEXISTENT_STUDENT"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error [student_not_found]" in captured.err
    assert_no_persian(captured.err)


def test_manage_process_photos_mocked_success(monkeypatch, capsys):
    enrollment.add_student("S3001", "محمد کریمی")
    monkeypatch.setattr(
        "backend.enrollment.process_photos",
        lambda student_id: {
            "accepted": 4,
            "rejected": [{"file": "blur.jpg", "reason": "no_face"}],
            "warnings": [{"message": "تعداد عکس‌ها زیاد بود"}],
            "embedding_saved": True,
        },
    )
    # en
    ret = manage.main(["process-photos", "--id", "S3001"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- Photos Processed" in captured.out
    assert "Accepted" in captured.out
    assert "4" in captured.out
    assert "Rejected" in captured.out
    assert "1" in captured.out
    assert "Embedding" in captured.out
    assert "Saved" in captured.out
    assert "Next step" in captured.out
    assert_no_persian(captured.out)

    # fa
    ret_fa = manage.main(["--lang", "fa", "process-photos", "--id", "S3001"])
    assert ret_fa == 0
    captured_fa = capsys.readouterr()
    assert "+-- پردازش تصاویر" in captured_fa.out
    assert "پذیرفته‌شده" in captured_fa.out
    assert "4" in captured_fa.out
    assert "Warning: Windows PowerShell console" in captured_fa.err


def test_manage_list_students_empty_and_populated(capsys):
    # 1. Empty (en)
    ret = manage.main(["list-students"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "No students found in the database." in captured.out
    assert_no_persian(captured.out)

    # 2. Empty (fa)
    ret_empty_fa = manage.main(["--lang", "fa", "list-students"])
    assert ret_empty_fa == 0
    captured_empty_fa = capsys.readouterr()
    assert "هیچ دانشجویی در سیستم ثبت نشده است." in captured_empty_fa.out
    assert "Warning: Windows PowerShell console" in captured_empty_fa.err

    # 3. Populated (en default - individual student cards)
    enrollment.add_student("S4001", "سارا احمدی", "مهندسی برق", "3")
    ret_pop = manage.main(["list-students"])
    assert ret_pop == 0
    captured_pop = capsys.readouterr()
    assert "+-- Student 1 of 1" in captured_pop.out
    assert "Student ID : S4001" in captured_pop.out
    assert "Term       : 3" in captured_pop.out
    assert "Photos     : 0" in captured_pop.out
    assert "Embedding  : No" in captured_pop.out
    assert "Total students: 1 | With embedding: 0 | Without: 1" in captured_pop.out
    assert_no_persian(captured_pop.out)

    # 4. Populated with --compact (en table)
    ret_compact = manage.main(["list-students", "--compact"])
    assert ret_compact == 0
    captured_compact = capsys.readouterr()
    assert "+------------+" in captured_compact.out
    assert "Student ID" in captured_compact.out
    assert "S4001" in captured_compact.out
    assert "(Persian)" in captured_compact.out  # Persian major replaced by ASCII placeholder
    assert "Total students: 1" in captured_compact.out
    assert_no_persian(captured_compact.out)

    # 5. Populated with --show-names (en)
    ret_names = manage.main(["list-students", "--show-names"])
    assert ret_names == 0
    captured_names = capsys.readouterr()
    assert "Names (Persian):" in captured_names.out
    assert "S4001:" in captured_names.out

    # 6. Populated (fa)
    ret_fa = manage.main(["--lang", "fa", "list-students"])
    assert ret_fa == 0
    captured_fa = capsys.readouterr()
    assert "+-- دانشجو 1 از 1" in captured_fa.out
    assert "مجموع دانشجویان: 1" in captured_fa.out
    assert "Warning: Windows PowerShell console" in captured_fa.err


def test_manage_status(capsys):
    enrollment.add_student("S8001", "نوید محمدی")
    session = session_manager.start_session(course_id=1, late_after_minutes=15)

    # 1. English status
    ret = manage.main(["status"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- System Status" in captured.out
    assert "Total students" in captured.out
    assert "1" in captured.out
    assert f"Session #{session['id']}" in captured.out
    assert "Excel reports" in captured.out
    assert_no_persian(captured.out)

    # 2. Persian status
    ret_fa = manage.main(["--lang", "fa", "status"])
    assert ret_fa == 0
    captured_fa = capsys.readouterr()
    assert "+-- وضعیت سامانه" in captured_fa.out
    assert "کل دانشجویان" in captured_fa.out
    assert "Warning: Windows PowerShell console" in captured_fa.err


def test_manage_session_summary(capsys):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    sid = session["id"]
    enrollment.add_student("S9001", "امید شریفی")
    attendance_service.log_attendance(sid, "S9001", source="face", confidence=0.32)

    # 1. English summary
    ret = manage.main(["session-summary", "--id", str(sid)])
    assert ret == 0
    captured = capsys.readouterr()
    assert f"+-- Session #{sid} Summary" in captured.out
    assert "Attendance Stats" in captured.out
    assert "Present" in captured.out
    assert "Late" in captured.out
    assert "Absent" in captured.out
    assert "Student Records" in captured.out
    assert "S9001" in captured.out
    assert "present (face)" in captured.out
    assert_no_persian(captured.out)

    # 2. Nonexistent session
    ret_non = manage.main(["session-summary", "--id", "99999"])
    assert ret_non == 1
    captured_non = capsys.readouterr()
    assert "Error [session_not_found]" in captured_non.err
    assert_no_persian(captured_non.err)

    # 3. Persian summary
    ret_fa = manage.main(["--lang", "fa", "session-summary", "--id", str(sid)])
    assert ret_fa == 0
    captured_fa = capsys.readouterr()
    assert f"+-- خلاصه جلسه شماره {sid}" in captured_fa.out
    assert "آمار حضور و غیاب" in captured_fa.out
    assert "Warning: Windows PowerShell console" in captured_fa.err


def test_manage_start_and_close_session(capsys):
    # 1. Start session
    ret_start = manage.main(["start-session", "--course-id", "1", "--late-after", "12"])
    assert ret_start == 0
    captured_start = capsys.readouterr()
    assert "+-- Session Started" in captured_start.out
    assert "Status" in captured_start.out
    assert "Active" in captured_start.out
    assert "Course ID" in captured_start.out
    assert "1" in captured_start.out
    assert "Late after" in captured_start.out
    assert "12 min" in captured_start.out
    assert "Next step" in captured_start.out
    assert_no_persian(captured_start.out)

    # 2. Try to start second active session
    ret_second = manage.main(["start-session", "--course-id", "1"])
    assert ret_second == 1
    captured_second = capsys.readouterr()
    assert "Error [session_already_active]" in captured_second.err
    assert_no_persian(captured_second.err)

    # 3. Close active session
    ret_close = manage.main(["close-session"])
    assert ret_close == 0
    captured_close = capsys.readouterr()
    assert "+-- Session Closed" in captured_close.out
    assert "Status" in captured_close.out
    assert "Closed" in captured_close.out
    assert "Next step" in captured_close.out
    assert_no_persian(captured_close.out)

    # 4. Close when no active session
    ret_no_active = manage.main(["close-session"])
    assert ret_no_active == 1
    captured_no_active = capsys.readouterr()
    assert "Error [no_active_session]" in captured_no_active.err
    assert_no_persian(captured_no_active.err)


def test_manage_close_session_by_id(capsys):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    sid = session["id"]

    ret = manage.main(["close-session", "--id", str(sid)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- Session Closed" in captured.out
    assert "Session ID" in captured.out
    assert str(sid) in captured.out
    assert_no_persian(captured.out)


def test_manage_report_session_report(capsys):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    enrollment.add_student("S5001", "رضا حسینی")
    attendance_service.log_attendance(session["id"], "S5001", source="manual")

    ret = manage.main(["report", "--session-id", str(session["id"])])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- Session Report Exported" in captured.out
    assert "Session ID" in captured.out
    assert str(session["id"]) in captured.out
    assert ".xlsx" in captured.out
    assert "Next step" in captured.out
    assert_no_persian(captured.out)


def test_manage_report_session_report_not_found(capsys):
    ret = manage.main(["report", "--session-id", "99999"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error [session_not_found]" in captured.err
    assert_no_persian(captured.err)


def test_manage_report_daily_success_and_shamsi_conversion(capsys):
    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    enrollment.add_student("S6001", "نرگس صادقی")
    attendance_service.log_attendance(session["id"], "S6001", source="manual")

    j_today = jdatetime.date.today()
    shamsi_str = f"{j_today.year:04d}-{j_today.month:02d}-{j_today.day:02d}"

    # 1. With explicit Shamsi date
    ret = manage.main(["report", "--daily", "--date", shamsi_str])
    assert ret == 0
    captured = capsys.readouterr()
    assert "+-- Daily Report Exported" in captured.out
    assert ".xlsx" in captured.out
    assert "Next step" in captured.out
    assert_no_persian(captured.out)

    # 2. Without --date (defaults to today)
    ret_def = manage.main(["report", "--daily"])
    assert ret_def == 0
    captured_def = capsys.readouterr()
    assert "+-- Daily Report Exported" in captured_def.out
    assert_no_persian(captured_def.out)


def test_manage_report_daily_invalid_dates(capsys):
    # Invalid format
    ret1 = manage.main(["report", "--daily", "--date", "not-a-date"])
    assert ret1 == 1
    captured1 = capsys.readouterr()
    assert "Error [invalid_input]" in captured1.err
    assert_no_persian(captured1.err)

    # Invalid calendar value (month 15)
    ret2 = manage.main(["report", "--daily", "--date", "1403-15-40"])
    assert ret2 == 1
    captured2 = capsys.readouterr()
    assert "Error [invalid_input]" in captured2.err
    assert_no_persian(captured2.err)


def test_manage_report_daily_empty(capsys):
    ret = manage.main(["report", "--daily", "--date", "1380-01-01"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error [report_empty]" in captured.err
    assert_no_persian(captured.err)


def test_manage_report_mutually_exclusive_args(capsys):
    ret1 = manage.main(["report"])
    assert ret1 != 0

    ret2 = manage.main(["report", "--session-id", "1", "--daily"])
    assert ret2 != 0


def test_manage_run_mocked(monkeypatch):
    mock_run = MagicMock()
    monkeypatch.setattr("uvicorn.run", mock_run)

    ret = manage.main(["run", "--host", "0.0.0.0", "--port", "8888"])
    assert ret == 0
    mock_run.assert_called_once_with(
        "backend.api.app:app",
        host="0.0.0.0",
        port=8888,
        workers=1,
        reload=False,
    )


def test_no_persian_in_en_mode_all_commands(capsys):
    """Strictly assert that no English command emits non-ASCII / Persian characters."""
    cmds = [
        ["init-db"],
        ["add-student", "--id", "P901", "--name", "سید علی موسوی", "--major", "مهندسی مکانیک", "--term", "5"],
        ["list-students"],
        ["list-students", "--compact"],
        ["status"],
        ["start-session", "--course-id", "1", "--late-after", "10"],
        ["session-summary", "--id", "1"],
        ["close-session"],
        ["report", "--session-id", "1"],
        ["report", "--daily"],
        ["delete-student", "--id", "P901"],
    ]
    for cmd in cmds:
        ret = manage.main(cmd)
        assert ret == 0, f"Command {cmd} failed with exit code {ret}"
        captured = capsys.readouterr()
        assert_no_persian(captured.out)
        assert_no_persian(captured.err)


# =========================================================================== #
# main_test.py tests
# =========================================================================== #


class DummyCapture:
    """Mock OpenCV VideoCapture for unit tests."""

    def __init__(self, opened: bool = True, frames_to_read: int = 4):
        self._opened = opened
        self._frames_left = frames_to_read
        self._released = False

    def isOpened(self) -> bool:
        return self._opened and not self._released

    def read(self):
        if not self._opened or self._frames_left <= 0:
            return False, None
        self._frames_left -= 1
        # 100x100 BGR dummy frame
        return True, np.zeros((100, 100, 3), dtype=np.uint8)

    def get(self, prop_id: int) -> float:
        return 30.0

    def release(self) -> None:
        self._released = True


def test_main_test_camera_test_only_success(capsys):
    cap = DummyCapture(opened=True, frames_to_read=1)
    ret = main_test.run_camera_test(source=0, cap_override=cap)
    assert ret == 0
    assert cap._released is True
    captured = capsys.readouterr()
    assert "Camera connected successfully:" in captured.out
    assert "100x100" in captured.out


def test_main_test_camera_test_only_failure(capsys):
    cap = DummyCapture(opened=False)
    ret = main_test.run_camera_test(source=0, cap_override=cap)
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error: Failed to open camera source '0'." in captured.err


def test_main_test_preview_mode(monkeypatch, capsys):
    """Preview mode detects faces and shows window, but does NOT write to database."""
    import cv2

    cap = DummyCapture(opened=True, frames_to_read=6)
    monkeypatch.setattr(cv2, "imshow", lambda win, img: None)
    monkeypatch.setattr(cv2, "waitKey", lambda delay: -1)

    mock_recognize = MagicMock(
        return_value=[
            {
                "student_id": "S101",
                "distance": 0.38,
                "box": (0.1, 0.9, 0.9, 0.1),
            },
            {
                "student_id": None,
                "distance": 0.85,
                "box": (0.2, 0.8, 0.8, 0.2),
            },
        ]
    )
    monkeypatch.setattr("backend.recognition.recognize_frame", mock_recognize)

    mock_process = MagicMock()
    monkeypatch.setattr("backend.attendance_service.process_recognition_result", mock_process)

    ret = main_test.run_live_loop(source=0, session_id=None, cap_override=cap, max_frames=6)
    assert ret == 0
    captured = capsys.readouterr()
    assert "Preview mode active" in captured.out
    assert "no database writes" in captured.out

    # Crucial assertion: process_recognition_result must NEVER be called in preview mode
    mock_process.assert_not_called()
    assert mock_recognize.called


def test_main_test_recording_mode_invalid_session(capsys):
    ret = main_test.run_live_loop(source=0, session_id=99999)
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error checking session:" in captured.err or "session_not_found" in captured.err


def test_main_test_recording_mode_closed_session(capsys):
    session = session_manager.start_session(course_id=1)
    session_manager.close_session(session["id"])

    ret = main_test.run_live_loop(source=0, session_id=session["id"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "not active" in captured.err


def test_main_test_recording_mode_active_session(monkeypatch, capsys):
    """Recording mode processes frames and calls process_recognition_result."""
    import cv2

    session = session_manager.start_session(course_id=1, late_after_minutes=10)
    sid = session["id"]
    enrollment.add_student("S6001", "امید محمدی")

    cap = DummyCapture(opened=True, frames_to_read=6)
    monkeypatch.setattr(cv2, "imshow", lambda win, img: None)
    monkeypatch.setattr(cv2, "waitKey", lambda delay: -1)

    matches_sample = [
        {
            "student_id": "S6001",
            "distance": 0.35,
            "box": (0.1, 0.9, 0.9, 0.1),
        }
    ]
    monkeypatch.setattr("backend.recognition.recognize_frame", lambda frame: matches_sample)

    mock_process = MagicMock(
        return_value={
            "recorded": ["S6001"],
            "already_present": [],
            "pending": {},
            "unknown_count": 0,
        }
    )
    monkeypatch.setattr("backend.attendance_service.process_recognition_result", mock_process)

    ret = main_test.run_live_loop(source=0, session_id=sid, cap_override=cap, max_frames=6)
    assert ret == 0
    captured = capsys.readouterr()
    assert f"Recording mode active for session {sid}" in captured.out
    assert "Attendance recorded: S6001" in captured.out

    # Crucial assertion: process_recognition_result was called with session_id and matches
    mock_process.assert_called_with(sid, matches_sample)


def test_main_test_main_cli_dispatch(monkeypatch):
    """Test CLI argument parsing and dispatching in main_test.main."""
    mock_test = MagicMock(return_value=0)
    mock_loop = MagicMock(return_value=0)
    monkeypatch.setattr("main_test.run_camera_test", mock_test)
    monkeypatch.setattr("main_test.run_live_loop", mock_loop)

    # 1. --camera-test-only
    ret1 = main_test.main(["--camera-test-only", "--camera-source", "1"])
    assert ret1 == 0
    mock_test.assert_called_once_with(1)

    # 2. default preview loop
    ret2 = main_test.main([])
    assert ret2 == 0
    mock_loop.assert_called_with(source=config.CAMERA_SOURCE, session_id=None)

    # 3. recording mode with session id
    ret3 = main_test.main(["--session-id", "5"])
    assert ret3 == 0
    mock_loop.assert_called_with(source=config.CAMERA_SOURCE, session_id=5)


def test_draw_label_persian_modifies_frame():
    """Verify draw_label successfully shapes and renders Persian text onto a frame."""
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    res = main_test.draw_label(
        frame=frame,
        text="علی رضایی",
        position=(10, 20),
        color=(0, 255, 0),
        font_size=18,
    )
    assert res is frame
    assert np.count_nonzero(frame) > 0


def test_draw_label_ascii_modifies_frame():
    """Verify draw_label works with ASCII labels."""
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    res = main_test.draw_label(
        frame=frame,
        text="Unknown",
        position=(10, 20),
        color=(0, 0, 255),
        font_size=18,
    )
    assert res is frame
    assert np.count_nonzero(frame) > 0


def test_draw_label_fallback_on_error(monkeypatch):
    """Verify draw_label gracefully falls back to cv2.putText if font/shaping fails."""
    monkeypatch.setattr("main_test._get_font", lambda font_size: None)
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    res = main_test.draw_label(
        frame=frame,
        text="محمد علوی",
        position=(10, 20),
        color=(0, 255, 0),
        fallback_ascii="S9999",
    )
    assert res is frame
    assert np.count_nonzero(frame) > 0


def test_load_student_names_database():
    """Verify load_student_names correctly returns student_id -> full_name mapping."""
    enrollment.add_student("S7001", "زهرا کریمی")
    enrollment.add_student("S7002", "سهراب سپهری")

    names = main_test.load_student_names()
    assert names.get("S7001") == "زهرا کریمی"
    assert names.get("S7002") == "سهراب سپهری"
