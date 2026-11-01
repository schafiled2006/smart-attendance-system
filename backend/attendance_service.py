"""Attendance logic, streak tracking, and manual adjustments.

Implemented in stage 6.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timedelta

from backend import config, database
from backend.errors import InvalidInputError, NoActiveSessionError, SessionNotFoundError
from backend.utils import now_tehran, to_iso, setup_logging

logger = logging.getLogger(__name__)

# Global streak tracker: session_id -> {student_id: streak_count}
streak_trackers: dict[int, dict[str, int]] = {}
_streak_lock = threading.Lock()


def reset_session_tracker(session_id: int) -> None:
    """Clear streak tracker for a specific session."""
    with _streak_lock:
        if session_id in streak_trackers:
            del streak_trackers[session_id]


def log_attendance(session_id: int, student_id: str, source: str = "face", confidence: float | None = None) -> bool:
    """Log attendance for a student in a session.
    
    Raises:
        NoActiveSessionError: if the session is not active.
        InvalidInputError: if source is not 'face' or 'manual'.
    """
    if source not in ("face", "manual"):
        raise InvalidInputError("منبع حضور باید 'face' یا 'manual' باشد.")
    
    setup_logging()
    connection = database.get_connection()
    try:
        # Check if session is active
        row = connection.execute(
            "SELECT status FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise SessionNotFoundError(session_id)
        if row["status"] != "active":
            raise NoActiveSessionError()

        # Check if student exists
        student_row = connection.execute(
            "SELECT student_id FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if student_row is None:
            raise InvalidInputError(f"دانشجویی با شناسه {student_id} یافت نشد.")

        checked_at = to_iso(now_tehran())
        try:
            connection.execute(
                "INSERT INTO attendance (session_id, student_id, checked_at, source, confidence) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, student_id, checked_at, source, confidence),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            # UNIQUE constraint failed (already present)
            connection.rollback()
            return False
        
        logger.info("Attendance logged: session_id=%s student_id=%s source=%s", session_id, student_id, source)
        return True
    finally:
        connection.close()


def remove_attendance(session_id: int, student_id: str) -> bool:
    """Remove attendance record for a student in a session.
    
    Raises:
        NoActiveSessionError: if the session is not active.
    """
    setup_logging()
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT status FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise SessionNotFoundError(session_id)
        if row["status"] != "active":
            raise NoActiveSessionError()

        cursor = connection.execute(
            "DELETE FROM attendance WHERE session_id = ? AND student_id = ?",
            (session_id, student_id),
        )
        connection.commit()
        if cursor.rowcount > 0:
            logger.info("Attendance removed: session_id=%s student_id=%s", session_id, student_id)
            return True
        return False
    finally:
        connection.close()


def get_session_attendance(session_id: int) -> list[dict]:
    """Get attendance status for all students in a session.
    
    Returns a list of dicts with:
    student_id, full_name, major, term, status, checked_at, source
    """
    connection = database.get_connection()
    try:
        session_row = connection.execute(
            "SELECT started_at, late_after_minutes FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session_row is None:
            raise SessionNotFoundError(session_id)
        
        started_at_str = session_row["started_at"]
        late_after_minutes = session_row["late_after_minutes"]
        
        # Parse started_at to datetime
        started_at = datetime.fromisoformat(started_at_str)
        late_threshold = started_at + timedelta(minutes=late_after_minutes)
        
        students = connection.execute(
            "SELECT student_id, full_name, major, term FROM students"
        ).fetchall()
        
        attendance_records = connection.execute(
            "SELECT student_id, checked_at, source FROM attendance WHERE session_id = ?",
            (session_id,)
        ).fetchall()
        
        attendance_map = {row["student_id"]: row for row in attendance_records}
        
        result = []
        for student in students:
            student_id = student["student_id"]
            record = attendance_map.get(student_id)
            
            if record is None:
                status = "absent"
                checked_at = None
                source = None
            else:
                checked_at_str = record["checked_at"]
                checked_at_dt = datetime.fromisoformat(checked_at_str)
                # مرز دقیق (برابر late_after_minutes) باید present باشد
                if checked_at_dt <= late_threshold:
                    status = "present"
                else:
                    status = "late"
                checked_at = checked_at_str
                source = record["source"]
            
            result.append({
                "student_id": student_id,
                "full_name": student["full_name"],
                "major": student["major"],
                "term": student["term"],
                "status": status,
                "checked_at": checked_at,
                "source": source,
            })
        
        return result
    finally:
        connection.close()


def get_session_summary(session_id: int) -> dict:
    """Get summary counts for a session."""
    attendance_list = get_session_attendance(session_id)
    total = len(attendance_list)
    present = sum(1 for a in attendance_list if a["status"] == "present")
    late = sum(1 for a in attendance_list if a["status"] == "late")
    absent = sum(1 for a in attendance_list if a["status"] == "absent")
    
    return {
        "total": total,
        "present": present,
        "late": late,
        "absent": absent,
    }


def process_recognition_result(session_id: int, matches: list[dict]) -> dict:
    """Process face recognition matches for an active session.
    
    Args:
        session_id: The active session ID.
        matches: List of dicts from recognition.py, each containing 'student_id' (str or None) and 'distance' (float).
        
    Returns:
        dict with keys: 'recorded', 'already_present', 'pending', 'unknown_count'
        
    Raises:
        NoActiveSessionError: if the session is not active.
    """
    setup_logging()
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT status FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise SessionNotFoundError(session_id)
        if row["status"] != "active":
            raise NoActiveSessionError()
            
        # Get already present students in this session
        present_students = {
            row["student_id"] 
            for row in connection.execute(
                "SELECT student_id FROM attendance WHERE session_id = ?", (session_id,)
            ).fetchall()
        }
    finally:
        connection.close()

    recorded = []
    already_present = []
    unknown_count = 0
    seen_in_frame = set()

    with _streak_lock:
        if session_id not in streak_trackers:
            streak_trackers[session_id] = {}
        tracker = streak_trackers[session_id]

        for match in matches:
            student_id = match.get("student_id")
            distance = match.get("distance")

            if student_id is None:
                unknown_count += 1
                logger.info("چهره ناشناس دیده شد (فاصله: %.3f)", distance)
                continue

            seen_in_frame.add(student_id)

            if student_id in present_students:
                already_present.append(student_id)
                continue

            # Increment streak
            tracker[student_id] = tracker.get(student_id, 0) + 1

            if tracker[student_id] >= config.REQUIRED_CONSECUTIVE_FRAMES:
                # Log attendance
                success = log_attendance(session_id, student_id, source="face", confidence=distance)
                if success:
                    recorded.append(student_id)
                    present_students.add(student_id)
                    del tracker[student_id]
                else:
                    # Should not happen due to present_students check, but just in case
                    already_present.append(student_id)
                    del tracker[student_id]

        # Reset streak for students not seen in this frame (delete to prevent memory leak)
        for student_id in list(tracker.keys()):
            if student_id not in seen_in_frame:
                del tracker[student_id]

        pending_copy = dict(tracker)

    return {
        "recorded": recorded,
        "already_present": already_present,
        "pending": pending_copy,
        "unknown_count": unknown_count,
    }
