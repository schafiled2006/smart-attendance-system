"""Stage 7 tests: report_service.py.

All tests use a temporary database and reports directory.
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest
import openpyxl

from backend import attendance_service, config, database, report_service, session_manager
from backend.errors import ReportEmptyError, SessionNotFoundError
from backend.utils import now_tehran, to_iso, to_jalali_str


@pytest.fixture(autouse=True)
def temp_db_and_reports(tmp_path, monkeypatch):
    """Isolate the database and reports directory before each test."""
    db_path = tmp_path / "stage7_test.db"
    monkeypatch.setenv("ATTENDANCE_DB", str(db_path))
    monkeypatch.setattr(config, "REPORTS_DIR", tmp_path)
    database.init_db()
    
    # Clear streak trackers
    attendance_service.streak_trackers.clear()
    
    yield tmp_path


def _create_course(title: str = "Test Course") -> int:
    connection = database.get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO courses (title) VALUES (?)",
            (title,),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


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


def test_export_session_report_structure_and_rtl(temp_db_and_reports):
    course_id = _create_course("ریاضی ۱")
    session = session_manager.start_session(course_id=course_id, late_after_minutes=10)
    _create_student("100", "Ali")
    _create_student("200", "Reza")
    
    attendance_service.log_attendance(session["id"], "100", source="face")
    
    # Manually insert a late attendance
    late_time = to_iso(now_tehran() + timedelta(minutes=15))
    connection = database.get_connection()
    try:
        connection.execute(
            "INSERT INTO attendance (session_id, student_id, checked_at, source) VALUES (?, ?, ?, ?)",
            (session["id"], "200", late_time, "manual")
        )
        connection.commit()
    finally:
        connection.close()
    
    file_path = report_service.export_session_report(session["id"])
    assert file_path.exists()
    
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    assert ws.sheet_view.rightToLeft is True
    
    # Check rows 1 to 5: headers, merged ranges, summary info
    assert "گزارش حضور و غیاب: ریاضی ۱" in str(ws["A1"].value)
    assert "تاریخ:" in str(ws["A2"].value)
    assert "ساعت شروع:" in str(ws["A2"].value)
    assert "حاضر: 1" in str(ws["A3"].value)
    assert "تأخیر: 1" in str(ws["A3"].value)
    assert "غایب: 0" in str(ws["A3"].value)
    assert "کل: 2" in str(ws["A3"].value)

    merged_str_ranges = [str(r) for r in ws.merged_cells.ranges]
    assert "A1:H1" in merged_str_ranges
    assert "A2:H2" in merged_str_ranges
    assert "A3:H3" in merged_str_ranges

    assert ws["A6"].value == "ردیف"
    assert ws["B6"].value == "شماره دانشجویی"
    assert ws["C6"].value == "نام و نام خانوادگی"
    assert ws["D6"].value == "رشته"
    assert ws["E6"].value == "ترم"
    assert ws["F6"].value == "وضعیت"
    assert ws["G6"].value == "ساعت ورود"
    assert ws["H6"].value == "روش ثبت"
    
    # Check sorting (numeric)
    assert ws["B7"].value == "100"
    assert ws["B8"].value == "200"
    
    # Check status
    assert ws["F7"].value == "حاضر"
    assert ws["F8"].value == "تأخیر"


def test_export_daily_report_multiple_sessions(temp_db_and_reports):
    course_id_1 = _create_course("Course A")
    course_id_2 = _create_course("Course B")
    
    _create_student("100", "Ali")
    
    # Session 1: start, log attendance, then close
    session1 = session_manager.start_session(course_id=course_id_1, late_after_minutes=10)
    attendance_service.log_attendance(session1["id"], "100", source="face")
    session_manager.close_session(session1["id"])
    
    # Session 2: start, log attendance, then close
    session2 = session_manager.start_session(course_id=course_id_2, late_after_minutes=10)
    attendance_service.log_attendance(session2["id"], "100", source="face")
    session_manager.close_session(session2["id"])
    
    date_iso = to_jalali_str(session1["started_at"]).replace('/', '-')
    
    file_path = report_service.export_daily_report(date_iso)
    assert file_path.exists()
    
    wb = openpyxl.load_workbook(file_path)
    assert len(wb.sheetnames) == 2
    
    # Check sheet names contain session ID and are cleaned
    assert any("1_" in name for name in wb.sheetnames)
    assert any("2_" in name for name in wb.sheetnames)

    # Detailed content check for each sheet
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        assert sheet.sheet_view.rightToLeft is True
        assert "گزارش حضور و غیاب:" in str(sheet["A1"].value)
        assert "تاریخ:" in str(sheet["A2"].value)
        assert "آمار:" in str(sheet["A3"].value)
        assert sheet["A6"].value == "ردیف"
        assert sheet["B6"].value == "شماره دانشجویی"
        assert sheet["B7"].value == "100"
        assert sheet["F7"].value == "حاضر"


def test_export_daily_report_empty_raises_error(temp_db_and_reports):
    date_iso = "1403-01-01" # Arbitrary past date
    with pytest.raises(ReportEmptyError):
        report_service.export_daily_report(date_iso)


def test_export_session_report_empty_session(temp_db_and_reports):
    course_id = _create_course("Empty Course")
    session = session_manager.start_session(course_id=course_id, late_after_minutes=10)
    
    file_path = report_service.export_session_report(session["id"])
    assert file_path.exists()
    
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    # Should have headers but no data rows
    assert ws["A7"].value is None


def test_export_session_report_nonexistent_session(temp_db_and_reports):
    with pytest.raises(SessionNotFoundError):
        report_service.export_session_report(9999)


def test_absent_students_have_empty_cells(temp_db_and_reports):
    course_id = _create_course("Test Course")
    session = session_manager.start_session(course_id=course_id, late_after_minutes=10)
    _create_student("300", "Absent Student")
    
    file_path = report_service.export_session_report(session["id"])
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    # Find the absent student row
    absent_row = None
    for row in range(7, 20):
        if ws.cell(row=row, column=2).value == "300":
            absent_row = row
            break
            
    assert absent_row is not None
    assert ws.cell(row=absent_row, column=6).value == "غایب"
    assert ws.cell(row=absent_row, column=7).value is None  # ساعت ورود خالی
    assert ws.cell(row=absent_row, column=8).value is None  # روش ثبت خالی