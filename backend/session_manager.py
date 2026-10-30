"""Session lifecycle management.

Implemented in stage 5.
"""
from __future__ import annotations

import logging
import sqlite3

from backend import config, database
from backend.errors import (
    InvalidInputError,
    NoActiveSessionError,
    SessionAlreadyActiveError,
    SessionClosedError,
    SessionNotFoundError,
)
from backend.utils import now_tehran, to_iso, setup_logging

logger = logging.getLogger(__name__)

SESSION_COLUMNS = ("id", "course_id", "started_at", "ended_at", "late_after_minutes", "status")


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict with exactly the table columns."""
    return {key: row[key] for key in row.keys()}


def _validate_late_after_minutes(value: int | None) -> int:
    """Return the effective late_after_minutes, applying defaults and validation."""
    if value is None:
        value = config.DEFAULT_LATE_AFTER_MINUTES
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidInputError("حد تأخير باید عدد صحیح باشد.")
    if value < 0 or value > 600:
        raise InvalidInputError("حد تأخير باید بین ۰ و ۶۰۰ دقیقه باشد.")
    return value


def start_session(course_id: int = 1, late_after_minutes: int | None = None) -> dict:
    """Start a new session.

    Raises:
        InvalidInputError: if the course does not exist or late_after_minutes
            is not an int in [0, 600].
        SessionAlreadyActiveError: if a session is already active.
    """
    late_after_minutes = _validate_late_after_minutes(late_after_minutes)
    setup_logging()

    connection = database.get_connection()
    try:
        # The course must exist.
        course = connection.execute(
            "SELECT id FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        if course is None:
            raise InvalidInputError(f"درس با شناسه {course_id} وجود ندارد.")

        started_at = to_iso(now_tehran())
        try:
            cursor = connection.execute(
                "INSERT INTO sessions (course_id, started_at, late_after_minutes, status) "
                "VALUES (?, ?, ?, 'active')",
                (course_id, started_at, late_after_minutes),
            )
            session_id = cursor.lastrowid
            connection.commit()
        except sqlite3.IntegrityError:
            # Partial unique index ux_one_active_session blocks a second active row.
            connection.rollback()
            raise SessionAlreadyActiveError()

        row = connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    finally:
        connection.close()

    logger.info(
        "Session started: id=%s course_id=%s late_after_minutes=%s",
        session_id,
        course_id,
        late_after_minutes,
    )
    return _row_to_dict(row)


def close_session(session_id: int | None = None) -> dict:
    """Close a session.

    If ``session_id`` is ``None`` the active session is closed.

    Raises:
        NoActiveSessionError: if ``session_id`` is None and no session is active.
        SessionNotFoundError: if the given id does not exist.
        SessionClosedError: if the given session is already closed.
    """
    setup_logging()
    connection = database.get_connection()
    try:
        if session_id is None:
            row = connection.execute(
                "SELECT * FROM sessions WHERE status = 'active' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row is None:
                raise NoActiveSessionError()
            session_id = row["id"]
        else:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise SessionNotFoundError(session_id)
            if row["status"] == "closed":
                raise SessionClosedError()

        ended_at = to_iso(now_tehran())
        connection.execute(
            "UPDATE sessions SET ended_at = ?, status = 'closed' WHERE id = ?",
            (ended_at, session_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    finally:
        connection.close()

    logger.info("Session closed: id=%s", session_id)
    return _row_to_dict(row)


def get_active_session() -> dict | None:
    """Return the active session, or ``None`` if there is none."""
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM sessions WHERE status = 'active' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return _row_to_dict(row)


def get_session(session_id: int) -> dict:
    """Return a session by id.

    Raises:
        SessionNotFoundError: if no session with that id exists.
    """
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise SessionNotFoundError(session_id)
    return _row_to_dict(row)


def list_sessions(limit: int = 50) -> list[dict]:
    """Return all sessions, newest first.

    Raises:
        InvalidInputError: if ``limit`` is not an int in [1, 500].
    """
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("حد تعداد باید عدد صحیح باشد.")
    if limit < 1 or limit > 500:
        raise InvalidInputError("حد تعداد باید بین ۱ و ۵۰۰ باشد.")

    connection = database.get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        connection.close()
    return [_row_to_dict(row) for row in rows]
