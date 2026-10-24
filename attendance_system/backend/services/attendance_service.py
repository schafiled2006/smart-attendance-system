import json
from datetime import datetime, timezone
from pathlib import Path
from ..config import DB_PATH, DEFAULT_LATE_THRESHOLD


def get_db():
    """Get a database connection."""
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def log_attendance(student_id: str, confidence: float,
                   camera_source: str = "laptop") -> dict:
    """
    Log attendance for a student.

    Rules:
        - If no active session → error
        - If already logged in this session → "قبلاً ثبت شده"
        - Compare current time with session start + late_threshold:
            - Before threshold → status = present
            - After threshold → status = late

    Returns:
        dict with attendance log result
    """
    # Check for active session
    active = get_active_session()
    if not active:
        return {
            "success": False,
            "error": "هیچ جلسه فعال وجود ندارد."
        }

    session_id = active["session_id"]
    start_time_str = active["start_time"]
    late_threshold = active.get("late_threshold_minutes", DEFAULT_LATE_THRESHOLD)

    # Parse session start time
    if start_time_str:
        try:
            # Handle ISO format
            if '+' in start_time_str or 'Z' in start_time_str:
                start_dt = datetime.fromisoformat(start_time_str)
            else:
                # Assume UTC if no timezone info
                start_dt = datetime.fromisoformat(start_time_str).replace(
                    tzinfo=timezone.utc
                )
        except (ValueError, TypeError) as e:
            return {
                "success": False,
                "error": f"خطا در تحلیل زمان شروع جلسه: {e}"
            }
    else:
        start_dt = datetime.now(timezone.utc)

    # Check if already logged in this session
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM attendance WHERE session_id = ? AND student_id = ?",
            (session_id, student_id)
        )
        existing = cursor.fetchone()

        if existing:
            conn.close()
            return {
                "success": False,
                "error": "قبلاً ثبت شده",
                "existing_record": {
                    "id": existing["id"],
                    "status": existing["status"],
                    "check_in_time": existing["check_in_time"],
                }
            }
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "error": f"خطا در بررسی تکراری: {e}"
        }

    # Determine status based on time threshold
    now = datetime.now(timezone.utc)
    elapsed_minutes = (now - start_dt).total_seconds() / 60.0

    if elapsed_minutes <= late_threshold:
        status = "present"
        # Set check_in_time to current time for present/late
        check_in_time = now.isoformat()
    else:
        status = "late"
        check_in_time = now.isoformat()

    # Record attendance
    try:
        cursor.execute(
            """INSERT INTO attendance (session_id, student_id, full_name,
               status, check_in_time, confidence, camera_source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                student_id,
                _get_student_full_name(student_id),
                status,
                check_in_time,
                round(confidence, 4) if confidence else None,
                camera_source,
                datetime.now(timezone.utc).isoformat()
            )
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "error": f"خطا در ثبت حضور: {e}"
        }

    # Get student full name
    full_name = _get_student_full_name(student_id)

    conn.close()

    return {
        "success": True,
        "session_id": session_id,
        "student_id": student_id,
        "full_name": full_name,
        "status": status,
        "check_in_time": check_in_time,
        "confidence": round(confidence, 4) if confidence else None,
        "camera_source": camera_source,
        "late_threshold_minutes": late_threshold,
        "message": f"حضور {status} ثبت شد."
    }


def mark_absent(session_id: str, student_id: str) -> dict:
    """
    Manually mark a student as absent for a session.

    Returns:
        dict with mark result
    """
    conn = get_db()
    cursor = conn.cursor()

    # Check if already logged
    cursor.execute(
        "SELECT * FROM attendance WHERE session_id = ? AND student_id = ?",
        (session_id, student_id)
    )
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {
            "success": False,
            "error": "قبلاً ثبت شده",
            "existing_status": existing["status"]
        }

    # Get student full name
    full_name = _get_student_full_name(student_id)

    try:
        cursor.execute(
            """INSERT INTO attendance (session_id, student_id, full_name,
               status, check_in_time, confidence, camera_source, created_at)
               VALUES (?, ?, ?, 'absent', NULL, NULL, 'manual', ?)""",
            (
                session_id,
                student_id,
                full_name,
                datetime.now(timezone.utc).isoformat()
            )
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "error": f"خطا در ثبت absent: {e}"
        }

    conn.close()
    return {
        "success": True,
        "session_id": session_id,
        "student_id": student_id,
        "full_name": full_name,
        "status": "absent",
        "message": f"دانشجو {full_name} به عنوان absent ثبت شد."
    }


def process_recognition_result(recognized_list: list, camera_source: str = "laptop") -> list:
    """
    Process recognition results from face engine.

    This is the bridge between face recognition and attendance logging.
    recognized_list = [{"student_id", "full_name", "confidence"}, ...]

    For each recognized student, log attendance if not already done.
    """
    results = []

    for recognition in recognized_list:
        student_id = recognition.get("student_id")
        full_name = recognition.get("full_name", "")
        confidence = recognition.get("confidence", 0.0)

        if not student_id:
            results.append({
                "student_id": None,
                "full_name": full_name or " ناشناس",
                "status": "absent",
                "error": "student_id missing"
            })
            continue

        # Try to log attendance
        log_result = log_attendance(student_id, confidence, camera_source)

        if not log_result.get("success"):
            # Already logged or error
            if "قبلاً ثبت شده" in log_result.get("error", ""):
                results.append({
                    "student_id": student_id,
                    "full_name": full_name,
                    "status": existing_status,
                    "message": "قبلاً ثبت شده"
                })
            else:
                results.append({
                    "student_id": student_id,
                    "full_name": full_name,
                    "status": "error",
                    "error": log_result.get("error")
                })
        else:
            results.append({
                "student_id": student_id,
                "full_name": full_name,
                "status": log_result.get("status", "present"),
                "check_in_time": log_result.get("check_in_time"),
                "confidence": log_result.get("confidence"),
                "message": log_result.get("message")
            })

    return results


def _get_student_full_name(student_id: str) -> str:
    """Helper to get student full name from database."""
    try:
        import sqlite3
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name FROM students WHERE student_id = ?",
            (student_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return student_id