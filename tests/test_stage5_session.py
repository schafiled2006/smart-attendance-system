"""Stage 5 tests: session_manager.py.

All tests use a temporary database via the ATTENDANCE_DB environment variable.
"""
from __future__ import annotations

import sqlite3

import pytest

from backend import config, database, session_manager
from backend.errors import (
    InvalidInputError,
    NoActiveSessionError,
    SessionAlreadyActiveError,
    SessionClosedError,
    SessionNotFoundError,
)

EXPECTED_SESSION_KEYS = {
    "id",
    "course_id",
    "started_at",
    "ended_at",
    "late_after_minutes",
    "status",
}


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """Isolate the database in a temporary file via ATTENDANCE_DB."""
    db_path = tmp_path / "stage5_test.db"
    monkeypatch.setenv("ATTENDANCE_DB", str(db_path))
    database.init_db()
    yield db_path


def test_start_and_read_back(temp_db, monkeypatch):
    result = session_manager.start_session(course_id=1, late_after_minutes=10)
    assert set(result.keys()) == EXPECTED_SESSION_KEYS
    assert result["course_id"] == 1
    assert result["late_after_minutes"] == 10
    assert result["status"] == "active"
    assert result["ended_at"] is None
    assert isinstance(result["id"], int)
    assert isinstance(result["started_at"], str)
    got = session_manager.get_session(result["id"])
    assert got == result
    active = session_manager.get_active_session()
    assert active is not None
    assert active["id"] == result["id"]


def test_second_start_rejected(temp_db, monkeypatch):
    session_manager.start_session(course_id=1, late_after_minutes=10)
    with pytest.raises(SessionAlreadyActiveError):
        session_manager.start_session(course_id=1, late_after_minutes=10)


def test_start_after_close_works(temp_db, monkeypatch):
    first = session_manager.start_session(course_id=1, late_after_minutes=10)
    session_manager.close_session(first["id"])
    second = session_manager.start_session(course_id=1, late_after_minutes=15)
    assert second["status"] == "active"
    assert second["id"] != first["id"]
    assert second["late_after_minutes"] == 15


def test_close_with_none_and_with_id(temp_db, monkeypatch):
    s = session_manager.start_session(course_id=1, late_after_minutes=10)
    closed = session_manager.close_session(s["id"])
    assert closed["status"] == "closed"
    assert closed["ended_at"] is not None
    assert session_manager.get_active_session() is None
    s2 = session_manager.start_session(course_id=1, late_after_minutes=10)
    closed2 = session_manager.close_session()
    assert closed2["id"] == s2["id"]
    assert closed2["status"] == "closed"


def test_closing_twice_raises(temp_db, monkeypatch):
    s = session_manager.start_session(course_id=1, late_after_minutes=10)
    session_manager.close_session(s["id"])
    with pytest.raises(SessionClosedError):
        session_manager.close_session(s["id"])


def test_unknown_ids(temp_db, monkeypatch):
    with pytest.raises(SessionNotFoundError):
        session_manager.get_session(99999)
    with pytest.raises(SessionNotFoundError):
        session_manager.close_session(99999)


def test_get_active_session_when_none(temp_db, monkeypatch):
    assert session_manager.get_active_session() is None


def test_default_late_after_minutes(temp_db, monkeypatch):
    result = session_manager.start_session(course_id=1)
    assert result["late_after_minutes"] == config.DEFAULT_LATE_AFTER_MINUTES


def test_invalid_course(temp_db, monkeypatch):
    with pytest.raises(InvalidInputError):
        session_manager.start_session(course_id=99999, late_after_minutes=10)

@pytest.mark.parametrize("late", [-1, 601, 2.5, "10", True])
def test_invalid_late_values(temp_db, monkeypatch, late):
    with pytest.raises(InvalidInputError):
        session_manager.start_session(course_id=1, late_after_minutes=late)


def test_list_order_and_limit(temp_db, monkeypatch):
    ids = []
    for _ in range(3):
        s = session_manager.start_session(course_id=1, late_after_minutes=10)
        ids.append(s["id"])
        session_manager.close_session(s["id"])
    listed = session_manager.list_sessions()
    assert len(listed) == 3
    assert listed[0]["id"] == ids[-1]
    assert listed[1]["id"] == ids[-2]
    assert listed[2]["id"] == ids[-3]
    limited = session_manager.list_sessions(limit=2)
    assert len(limited) == 2
    assert limited[0]["id"] == ids[-1]
    assert limited[1]["id"] == ids[-2]


@pytest.mark.parametrize("limit", [0, 501, 1.5, "10", True])
def test_invalid_limit(temp_db, monkeypatch, limit):
    with pytest.raises(InvalidInputError):
        session_manager.list_sessions(limit=limit)


def test_partial_unique_index_blocks_two_active_rows_raw_sql(temp_db, monkeypatch):
    connection = database.get_connection()
    try:
        connection.execute(
            "INSERT INTO sessions (course_id, started_at, late_after_minutes, status) "
            "VALUES (1, '2026-10-24T10:00:00+03:30', 10, 'active')"
        )
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sessions (course_id, started_at, late_after_minutes, status) "
                "VALUES (1, '2026-10-24T11:00:00+03:30', 10, 'active')"
            )
        connection.rollback()
    finally:
        connection.close()