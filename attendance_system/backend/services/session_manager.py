import json
from datetime import datetime, timezone
from pathlib import Path
from ..config import DB_PATH


def get_db():
    """Get a database connection."""
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def start_session(course_id: int, late_threshold_minutes: int = 10,
                  note: str = "") -> dict:
    """
    Start a new attendance session.

    Args:
        course_id: ID of the course
        late_threshold_minutes: Threshold in minutes (default 10)
        note: Optional note

    Returns:
        dict with session_id and session info
    """
    conn = get_db()
    cursor = conn.cursor()
    session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    try:
        cursor.execute(
            """INSERT INTO sessions (session_id, course_id, start_time, status,
               late_threshold_minutes, note, created_at)
               VALUES (?, ?, ?, 'active', ?, ?, ?)""",
            (session_id, course_id, datetime.now(timezone.utc).isoformat(),
             late_threshold_minutes, note,
             datetime.now(timezone.utc).isoformat())
        )
        conn.commit()

        # Return session info
        cursor.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        session_dict = dict(row) if row else {}
    finally:
        conn.close()

    return {
        "session_id": session_id,
        "course_id": course_id,
        "start_time": session_dict.get("start_time"),
        "status": session_dict.get("status"),
        "late_threshold_minutes": session_dict.get("late_threshold_minutes", 10),
        "note": session_dict.get("note", ""),
        "created_at": session_dict.get("created_at"),
    }


def close_session(session_id: str = None) -> dict:
    """
    Close an attendance session.

    If session_id is None, closes the active session.

    Returns:
        dict with close status
    """
    conn = get_db()
    cursor = conn.cursor()

    if session_id is None:
        # Close the active session
        cursor.execute(
            "UPDATE sessions SET status = 'closed' WHERE status = 'active'"
        )
        conn.commit()
        closed_count = cursor.rowcount
        return {
            "success": True,
            "closed_sessions": closed_count,
            "message": f"{closed_count} جلسه فعال بسته شد."
        }
    else:
        # Close specific session
        cursor.execute(
            "UPDATE sessions SET status = 'closed' WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        closed_count = cursor.rowcount
        return {
            "success": True,
            "closed_sessions": closed_count,
            "message": f"{closed_count} جلسه (شن {session_id}) بسته شد."
        }


def get_active_session() -> dict | None:
    """
    Get the currently active session.

    Returns:
        dict with session info, or None if no active session
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM sessions WHERE status = 'active' ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Error getting active session: {e}")
        conn.close()
        return None