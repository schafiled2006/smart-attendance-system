import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "attendance.db"


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with all required tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            major TEXT,
            term TEXT,
            embedding_file TEXT,
            created_at TEXT
        )
    """)

    # Courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE,
            title TEXT NOT NULL,
            teacher TEXT,
            created_at TEXT
        )
    """)

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            course_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL,
            late_threshold_minutes INTEGER DEFAULT 10,
            note TEXT,
            created_at TEXT
        )
    """)

    # Attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            full_name TEXT,
            status TEXT NOT NULL,
            check_in_time TEXT,
            confidence REAL,
            camera_source TEXT,
            created_at TEXT,
            UNIQUE(session_id, student_id)
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_course ON sessions(course_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)")

    conn.commit()
    conn.close()


def check_db_health():
    """Check database health and return status."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sessions")
        session_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cursor.fetchone()[0]
        conn.close()
        return {
            "status": "healthy",
            "students": student_count,
            "courses": course_count,
            "sessions": session_count,
            "attendance_records": attendance_count,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}