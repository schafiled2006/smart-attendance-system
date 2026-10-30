"""SQL table definitions and row dataclasses."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

STUDENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS students (
  student_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  major TEXT NOT NULL DEFAULT '',
  term TEXT NOT NULL DEFAULT '',
  embedding_path TEXT,
  photo_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
""".strip()

COURSES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  teacher TEXT NOT NULL DEFAULT '',
  room TEXT NOT NULL DEFAULT ''
);
""".strip()

SESSIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL REFERENCES courses(id),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  late_after_minutes INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','closed'))
);
""".strip()

ACTIVE_SESSION_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS ux_one_active_session
  ON sessions(status) WHERE status = 'active';
""".strip()

ATTENDANCE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  student_id TEXT NOT NULL REFERENCES students(student_id),
  checked_at TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('face','manual')),
  confidence REAL,
  UNIQUE (session_id, student_id)
);
""".strip()

SCHEMA_SQL = "\n\n".join(
    [
        STUDENTS_TABLE_SQL,
        COURSES_TABLE_SQL,
        SESSIONS_TABLE_SQL,
        ACTIVE_SESSION_INDEX_SQL,
        ATTENDANCE_TABLE_SQL,
    ]
)


@dataclass
class Student:
    student_id: str
    full_name: str
    major: str = ""
    term: str = ""
    embedding_path: str | None = None
    photo_count: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Student":
        return cls(
            student_id=row["student_id"],
            full_name=row["full_name"],
            major=row["major"],
            term=row["term"],
            embedding_path=row["embedding_path"],
            photo_count=row["photo_count"],
            created_at=row["created_at"],
        )


@dataclass
class Course:
    id: int
    title: str
    teacher: str = ""
    room: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Course":
        return cls(
            id=row["id"],
            title=row["title"],
            teacher=row["teacher"],
            room=row["room"],
        )


@dataclass
class Session:
    id: int
    course_id: int
    started_at: str
    late_after_minutes: int
    status: str
    ended_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Session":
        return cls(
            id=row["id"],
            course_id=row["course_id"],
            started_at=row["started_at"],
            late_after_minutes=row["late_after_minutes"],
            status=row["status"],
            ended_at=row["ended_at"],
        )


@dataclass
class AttendanceRecord:
    id: int
    session_id: int
    student_id: str
    checked_at: str
    source: str
    confidence: float | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AttendanceRecord":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            student_id=row["student_id"],
            checked_at=row["checked_at"],
            source=row["source"],
            confidence=row["confidence"],
        )
