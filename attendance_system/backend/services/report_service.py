import json
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from bidi.algorithm import get_display  # برای پشتیبانی از متن فارسی
import jdatetime

from ..config import DB_PATH
from ..database import get_db


def export_session_excel(session_id: str) -> dict:
    """
    Export session attendance to Excel file.

    Features:
        - Complete student list for the class
        - Columns: student_id | full_name | major | term | status | check_in_time | confidence
        - Persian (Jalali) date in filename and within the sheet
        - Right-to-left sheet for Persian text

    Returns:
        dict with file path and metadata
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get session info
    cursor.execute(
        "SELECT s.*, c.title as course_title FROM sessions s "
        "LEFT JOIN courses c ON s.course_id = c.id "
        "WHERE s.session_id = ?",
        (session_id,)
    )
    session_row = cursor.fetchone()

    if not session_row:
        conn.close()
        return {
            "success": False,
            "error": f"Session {session_id} not found."
        }

    # Get all students in the session
    cursor.execute(
        """SELECT a.student_id, s.full_name, s.major, s.term,
               a.status, a.check_in_time, a.confidence
          FROM attendance a
          JOIN students s ON a.student_id = s.student_id
          WHERE a.session_id = ?
          ORDER BY s.full_name""",
        (session_id,)
    )
    attendance_rows = cursor.fetchall()

    # Get all students enrolled in the course (for complete list)
    cursor.execute(
        """SELECT s.student_id, s.full_name, s.major, s.term
          FROM students s
          JOIN courses c ON s.major = c.title  -- approximate link
          WHERE c.id = ?
          ORDER BY s.full_name""",
        (session_row["course_id"],)
    )
    all_students = cursor.fetchall()

    conn.close()

    # Build data for Excel
    # Create a mapping of student_id -> attendance record
    attendance_map = {}
    for row in attendance_rows:
        attendance_map[row["student_id"]] = {
            "status": row["status"],
            "check_in_time": row["check_in_time"],
            "confidence": row["confidence"],
        }

    # Build complete records list
    records = []
    for student in all_students:
        student_id = student["student_id"]
        record = {
            "student_id": student["student_id"],
            "full_name": student["full_name"],
            "major": student.get("major") or "",
            "term": student.get("term") or "",
        }

        # Add attendance info
        if student_id in attendance_map:
            record["status"] = attendance_map[student_id]["status"]
            record["check_in_time"] = attendance_map[student_id]["check_in_time"]
            record["confidence"] = attendance_map[student_id]["confidence"]
        else:
            record["status"] = "absent"
            record["check_in_time"] = None
            record["confidence"] = None

        records.append(record)

    # Calculate statistics
    present_count = sum(1 for r in records if r.get("status") == "present")
    late_count = sum(1 for r in records if r.get("status") == "late")
    absent_count = sum(1 for r in records if r.get("status") == "absent")
    total_students = len(records)

    # Generate filename with Persian date
    now = datetime.now()
    jalali_date = jdatetime.date.fromgregorian(date=now)
    filename = f"raport_{session_id}_{jalali_date.strftime('%Y_%m_%d')}.xlsx"
    filename = filename.replace(" ", "_")

    # Define Excel file path
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_path = reports_dir / filename

    # Create Excel using pandas
    df = pd.DataFrame(records)
    # Reorder columns as specified
    df = df[["student_id", "full_name", "major", "term", "status",
             "check_in_time", "confidence"]]

    # Write to Excel with openpyxl engine for formatting
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="raport")

        # Additional formatting with openpyxl
        workbook = writer.book
        worksheet = writer.sheets["raport"]

        # Set column widths
        column_widths = {
            "A": 20,  # student_id
            "B": 25,  # full_name
            "C": 15,  # major
            "D": 12,  # term
            "E": 15,  # status
            "F": 20,  # check_in_time
            "G": 15,  # confidence
        }
        for col_letter, width in column_widths.items():
            worksheet.column_dimensions[col_letter].width = width

        # Right-to-left handling for Persian
        # Mark the sheet as right-to-left
        worksheet.sheet_properties.pageSetup.rightToLeft = True

        # Format status column with Persian colors/labels if needed
        from openpyxl.styles import Font, Alignment, PatternFill
        status_font = Font(name="B Nazanin", size=11)
        status_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for row_idx in range(2, len(records) + 2):  # skip header
            status_cell = worksheet.cell(row=row_idx, column=5)  # status column
            status_val = status_cell.value

            # Set font for status column
            status_cell.font = status_font
            status_cell.alignment = status_alignment

            # Color-code status
            if status_val == "present":
                status_cell.fill = PatternFill(
                    start_color="C6EFCE", end_color="C6EFCE",
                    fill_type="solid"
                )
            elif status_val == "late":
                status_cell.fill = PatternFill(
                    start_color="FFEB9C", end_color="FFEB9C",
                    fill_type="solid"
                )
            elif status_val == "absent":
                status_cell.fill = PatternFill(
                    start_color="FFC7CE", end_color="FFC7CE",
                    fill_type="solid"
                )

    # Prepare summary info
    summary = {
        "session_id": session_id,
        "course_title": session_row["course_title"],
        "date_jalali": jalali_date.strftime("%Y/%m/%d"),
        "date_gregorian": now.strftime("%Y/%m/%d"),
        "file_path": str(file_path),
        "total_students": total_students,
        "present_count": present_count,
        "late_count": late_count,
        "absent_count": absent_count,
        "records": records,
    }

    return {
        "success": True,
        "file_path": str(file_path),
        "filename": filename,
        "summary": summary,
        "message": f"گزارش اکسل با موفقیت ایجاد شد: {filename}"
    }