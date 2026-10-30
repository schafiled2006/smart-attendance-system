"""SQLite connection helpers and database initialization."""
from __future__ import annotations

import sqlite3

from backend import config
from backend.models import SCHEMA_SQL

DEFAULT_COURSE_TITLE = "کلاس اصلی"


def get_connection() -> sqlite3.Connection:
    """Open the configured database with foreign keys on and Row access."""
    db_path = config.get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create tables/indexes and the default course. Safe to call repeatedly."""
    connection = get_connection()
    try:
        connection.executescript(SCHEMA_SQL)
        row = connection.execute(
            "SELECT COUNT(*) AS course_count FROM courses"
        ).fetchone()
        if row["course_count"] == 0:
            connection.execute(
                "INSERT INTO courses (title, teacher, room) VALUES (?, ?, ?)",
                (DEFAULT_COURSE_TITLE, "", ""),
            )
        connection.commit()
    finally:
        connection.close()
