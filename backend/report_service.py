"""Report generation service for Excel exports.

Implemented in stage 7.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import jdatetime
import openpyxl
from openpyxl.styles import Alignment, Font

from backend import config, database
from backend.attendance_service import get_session_attendance, get_session_summary
from backend.errors import ReportEmptyError, SessionNotFoundError
from backend.session_manager import get_session
from backend.utils import parse_iso, setup_logging

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "present": "حاضر",
    "late": "تأخیر",
    "absent": "غایب",
}

SOURCE_MAP = {
    "face": "چهره",
    "manual": "دستی",
}


def _get_course_title(course_id: int) -> str:
    """Get course title by ID."""
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT title FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        return row["title"] if row else f"درس {course_id}"
    finally:
        connection.close()


def _write_session_to_sheet(ws, session: dict, attendance: list[dict], summary: dict) -> None:
    """Write session attendance data to a worksheet."""
    ws.sheet_view.rightToLeft = True
    
    # Header info
    dt = parse_iso(session["started_at"])
    jalali = jdatetime.datetime.fromgregorian(datetime=dt)
    date_str = f"{jalali.year:04d}/{jalali.month:02d}/{jalali.day:02d}"
    time_str = f"{jalali.hour:02d}:{jalali.minute:02d}"
    
    course_title = _get_course_title(session["course_id"])
    
    ws["A1"] = f"گزارش حضور و غیاب: {course_title}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"تاریخ: {date_str} | ساعت شروع: {time_str}"
    ws["A3"] = f"آمار: حاضر: {summary['present']} | تأخیر: {summary['late']} | غایب: {summary['absent']} | کل: {summary['total']}"
    
    # Column headers
    headers = ["ردیف", "شماره دانشجویی", "نام و نام خانوادگی", "رشته", "ترم", "وضعیت", "ساعت ورود", "روش ثبت"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        
    # Sort attendance
    is_all_numeric = all(str(a["student_id"]).isdigit() for a in attendance)
    sorted_attendance = sorted(
        attendance, 
        key=lambda x: int(x["student_id"]) if is_all_numeric else str(x["student_id"])
    )
    
    # Write rows
    for row_num, record in enumerate(sorted_attendance, 7):
        ws.cell(row=row_num, column=1, value=row_num - 6)
        ws.cell(row=row_num, column=2, value=record["student_id"])
        ws.cell(row=row_num, column=3, value=record["full_name"])
        ws.cell(row=row_num, column=4, value=record["major"])
        ws.cell(row=row_num, column=5, value=record["term"])
        ws.cell(row=row_num, column=6, value=STATUS_MAP.get(record["status"], record["status"]))
        
        if record["checked_at"]:
            checked_dt = parse_iso(record["checked_at"])
            ws.cell(row=row_num, column=7, value=checked_dt.strftime("%H:%M"))
        else:
            ws.cell(row=row_num, column=7, value="")
            
        if record["source"]:
            ws.cell(row=row_num, column=8, value=SOURCE_MAP.get(record["source"], record["source"]))
        else:
            ws.cell(row=row_num, column=8, value="")
            
    # Adjust column widths
    column_widths = [8, 15, 25, 15, 10, 10, 12, 10]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width


def export_session_report(session_id: int) -> Path:
    """Export attendance report for a specific session.
    
    Args:
        session_id: The ID of the session.
        
    Returns:
        Path to the generated Excel file.
        
    Raises:
        SessionNotFoundError: If the session does not exist.
    """
    setup_logging()
    session = get_session(session_id)
    attendance = get_session_attendance(session_id)
    summary = get_session_summary(session_id)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "گزارش جلسه"
    
    _write_session_to_sheet(ws, session, attendance, summary)
    
    # Generate filename
    dt = parse_iso(session["started_at"])
    jalali = jdatetime.datetime.fromgregorian(datetime=dt)
    date_str = f"{jalali.year:04d}-{jalali.month:02d}-{jalali.day:02d}"
    time_str = f"{jalali.hour:02d}{jalali.minute:02d}"
    filename = f"attendance_session{session_id}_{date_str}_{time_str}.xlsx"
    
    file_path = config.REPORTS_DIR / filename
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(file_path)
    
    logger.info("Session report exported: %s", file_path)
    return file_path


def export_daily_report(date_iso: str) -> Path:
    """Export daily attendance report for all sessions on a given Jalali date.
    
    Args:
        date_iso: The Jalali date in YYYY-MM-DD format.
        
    Returns:
        Path to the generated Excel file.
        
    Raises:
        ReportEmptyError: If no sessions exist for the given date.
    """
    setup_logging()
    
    # Get all sessions and filter by Jalali date
    connection = database.get_connection()
    try:
        rows = connection.execute("SELECT * FROM sessions ORDER BY started_at").fetchall()
    finally:
        connection.close()
        
    sessions = []
    for row in rows:
        dt = parse_iso(row["started_at"])
        jalali = jdatetime.datetime.fromgregorian(datetime=dt)
        jalali_date_str = f"{jalali.year:04d}-{jalali.month:02d}-{jalali.day:02d}"
        if jalali_date_str == date_iso:
            sessions.append(dict(row))
            
    if not sessions:
        raise ReportEmptyError()
        
    wb = openpyxl.Workbook()
    # Remove default sheet
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    for session in sessions:
        attendance = get_session_attendance(session["id"])
        summary = get_session_summary(session["id"])
        
        course_title = _get_course_title(session["course_id"])
        # Clean sheet name: remove forbidden chars, limit to 31, ensure uniqueness with session ID
        clean_title = re.sub(r'[\\/:*?"\[\]]', '', f"{session['id']}_{course_title}")
        clean_title = clean_title[:31]
        
        ws = wb.create_sheet(title=clean_title)
        _write_session_to_sheet(ws, session, attendance, summary)
        
    filename = f"daily_report_{date_iso}.xlsx"
    file_path = config.REPORTS_DIR / filename
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(file_path)
    
    logger.info("Daily report exported: %s", file_path)
    return file_path