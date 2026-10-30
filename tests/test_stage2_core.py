"""Stage 2 tests: utilities, database schema/initialization and models."""
from __future__ import annotations

import logging
import re
import sqlite3
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from backend import config, database, models, utils

TEHRAN = ZoneInfo("Asia/Tehran")


@pytest.fixture()
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "stage2_test.db"
    monkeypatch.setenv("ATTENDANCE_DB", str(db_path))
    database.init_db()
    connection = database.get_connection()
    try:
        yield connection, db_path
    finally:
        connection.close()


def _insert_student(
    connection: sqlite3.Connection,
    student_id: str = "40123456",
    full_name: str = "دانشجوی تست",
) -> None:
    connection.execute(
        "INSERT INTO students (student_id, full_name, created_at) VALUES (?, ?, ?)",
        (student_id, full_name, utils.to_iso(utils.now_tehran())),
    )
    connection.commit()


def _insert_session(
    connection: sqlite3.Connection, status: str = "active"
) -> int:
    connection.execute(
        "INSERT INTO sessions (course_id, started_at, late_after_minutes, status) "
        "VALUES (1, ?, 10, ?)",
        ("2026-10-24T10:00:00+03:30", status),
    )
    connection.commit()
    return connection.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]


# --------------------------------------------------------------------------- #
# utils
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("۰۱۲۳۴۵۶۷۸۹", "0123456789"),
        ("٠١٢٣٤٥٦٧٨٩", "0123456789"),
        ("شماره ۱۲۳ و 456", "شماره 123 و 456"),
        ("ASCII only 123", "ASCII only 123"),
        ("", ""),
    ],
)
def test_normalize_digits(raw: str, expected: str) -> None:
    assert utils.normalize_digits(raw) == expected


def test_now_tehran_is_aware_tehran_time() -> None:
    now = utils.now_tehran()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(hours=3, minutes=30)
    assert now.tzinfo.key == "Asia/Tehran"


def test_to_iso_formats_tehran_offset() -> None:
    dt = datetime(2026, 10, 24, 10, 5, tzinfo=TEHRAN)
    value = utils.to_iso(dt)
    assert value == "2026-10-24T10:05:00+03:30"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+03:30", value)


def test_to_iso_assumes_tehran_for_naive_datetime() -> None:
    assert (
        utils.to_iso(datetime(2026, 10, 24, 10, 5))
        == "2026-10-24T10:05:00+03:30"
    )


def test_parse_iso_roundtrip() -> None:
    original = datetime(2026, 10, 24, 10, 5, tzinfo=TEHRAN)
    assert utils.parse_iso(utils.to_iso(original)) == original


def test_parse_iso_handles_naive_and_utc_strings() -> None:
    naive = utils.parse_iso("2026-10-24T10:05:00")
    assert naive.utcoffset() == timedelta(hours=3, minutes=30)

    utc = utils.parse_iso("2026-10-24T06:35:00+00:00")
    assert utils.to_iso(utc) == "2026-10-24T10:05:00+03:30"


def test_to_jalali_str_without_time() -> None:
    dt = datetime(2024, 3, 20, 10, 30, tzinfo=TEHRAN)
    assert utils.to_jalali_str(dt) == "1403/01/01"
    assert utils.to_jalali_str("2024-03-20T10:30:00+03:30") == "1403/01/01"


def test_to_jalali_str_with_time_uses_ascii_digits() -> None:
    result = utils.to_jalali_str("2024-03-20T10:30:00+03:30", with_time=True)
    assert result == "1403/01/01 10:30"
    assert result.isascii()


def test_setup_logging_writes_rotating_utf8_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_file = tmp_path / "logs" / "app.log"
    monkeypatch.setattr(config, "LOG_FILE", log_file)

    utils.setup_logging()
    root = logging.getLogger()
    handler = next(
        item
        for item in root.handlers
        if isinstance(item, RotatingFileHandler)
        and Path(item.baseFilename) == log_file.resolve()
    )
    try:
        assert handler.maxBytes == 1_048_576
        assert handler.backupCount == 3
        assert handler.encoding.lower() == "utf-8"

        logging.getLogger("stage2.test").info("پیام تست لاگ")
        handler.flush()
        assert "پیام تست لاگ" in log_file.read_text(encoding="utf-8")
    finally:
        root.removeHandler(handler)
        handler.close()

    handlers_before = len(logging.getLogger().handlers)
    utils.setup_logging()
    assert len(logging.getLogger().handlers) == handlers_before


# --------------------------------------------------------------------------- #
# database
# --------------------------------------------------------------------------- #
def test_connection_uses_temp_db_and_pragmas(temp_db) -> None:
    connection, db_path = temp_db
    assert db_path.exists()
    assert config.get_db_path() == db_path.resolve()

    database_row = connection.execute("PRAGMA database_list").fetchone()
    assert Path(database_row["file"]).resolve() == db_path.resolve()
    assert connection.row_factory is sqlite3.Row
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_init_db_creates_all_tables(temp_db) -> None:
    connection, _ = temp_db
    names = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"students", "courses", "sessions", "attendance"} <= names


@pytest.mark.parametrize(
    ("table", "columns"),
    [
        (
            "students",
            [
                "student_id",
                "full_name",
                "major",
                "term",
                "embedding_path",
                "photo_count",
                "created_at",
            ],
        ),
        ("courses", ["id", "title", "teacher", "room"]),
        (
            "sessions",
            [
                "id",
                "course_id",
                "started_at",
                "ended_at",
                "late_after_minutes",
                "status",
            ],
        ),
        (
            "attendance",
            [
                "id",
                "session_id",
                "student_id",
                "checked_at",
                "source",
                "confidence",
            ],
        ),
    ],
)
def test_table_columns_match_spec(temp_db, table: str, columns: list[str]) -> None:
    connection, _ = temp_db
    actual = [
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})")
    ]
    assert actual == columns


def test_student_defaults_are_applied(temp_db) -> None:
    connection, _ = temp_db
    connection.execute(
        "INSERT INTO students (student_id, full_name, created_at) "
        "VALUES ('40222', 'علی رضایی', '2026-10-24T10:00:00+03:30')"
    )
    connection.commit()

    row = connection.execute(
        "SELECT * FROM students WHERE student_id = '40222'"
    ).fetchone()
    assert row["major"] == ""
    assert row["term"] == ""
    assert row["photo_count"] == 0
    assert row["embedding_path"] is None


def test_init_db_is_idempotent_and_creates_default_course(temp_db) -> None:
    connection, _ = temp_db
    database.init_db()
    database.init_db()

    rows = connection.execute("SELECT * FROM courses").fetchall()
    assert len(rows) == 1
    assert rows[0]["title"] == "کلاس اصلی"
    assert rows[0]["teacher"] == ""
    assert rows[0]["room"] == ""


def test_one_active_session_index_exists(temp_db) -> None:
    connection, _ = temp_db
    indexes = {
        row["name"]: row
        for row in connection.execute("PRAGMA index_list(sessions)")
    }
    assert "ux_one_active_session" in indexes
    assert indexes["ux_one_active_session"]["unique"] == 1

    sql = connection.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type = 'index' AND name = 'ux_one_active_session'"
    ).fetchone()["sql"]
    assert "WHERE status = 'active'" in sql


def test_only_one_active_session_allowed(temp_db) -> None:
    connection, _ = temp_db
    first_id = _insert_session(connection)

    with pytest.raises(sqlite3.IntegrityError):
        _insert_session(connection)
    connection.rollback()

    connection.execute(
        "UPDATE sessions SET status = 'closed', ended_at = ? WHERE id = ?",
        ("2026-10-24T10:30:00+03:30", first_id),
    )
    connection.commit()

    _insert_session(connection)
    _insert_session(connection, status="closed")


def test_session_status_check_constraint(temp_db) -> None:
    connection, _ = temp_db
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO sessions (course_id, started_at, late_after_minutes, status) "
            "VALUES (1, '2026-10-24T10:00:00+03:30', 10, 'bogus')"
        )
    connection.rollback()


def test_attendance_unique_per_session_and_student(temp_db) -> None:
    connection, _ = temp_db
    _insert_student(connection)
    session_id = _insert_session(connection)
    insert_sql = (
        "INSERT INTO attendance (session_id, student_id, checked_at, source) "
        "VALUES (?, ?, ?, 'face')"
    )
    connection.execute(
        insert_sql,
        (session_id, "40123456", "2026-10-24T10:01:00+03:30"),
    )
    connection.commit()

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            insert_sql,
            (session_id, "40123456", "2026-10-24T10:02:00+03:30"),
        )
    connection.rollback()


def test_attendance_foreign_keys_and_source_check(temp_db) -> None:
    connection, _ = temp_db
    _insert_student(connection)
    session_id = _insert_session(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO attendance (session_id, student_id, checked_at, source) "
            "VALUES (?, '99999999', '2026-10-24T10:01:00+03:30', 'face')",
            (session_id,),
        )
    connection.rollback()

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO attendance (session_id, student_id, checked_at, source) "
            "VALUES (?, '40123456', '2026-10-24T10:01:00+03:30', 'camera')",
            (session_id,),
        )
    connection.rollback()


# --------------------------------------------------------------------------- #
# models
# --------------------------------------------------------------------------- #
def test_dataclasses_from_rows(temp_db) -> None:
    connection, _ = temp_db
    _insert_student(connection, "40222", "علی رضایی")
    session_id = _insert_session(connection)
    connection.execute(
        "INSERT INTO attendance (session_id, student_id, checked_at, source) "
        "VALUES (?, '40222', '2026-10-24T10:05:00+03:30', 'manual')",
        (session_id,),
    )
    connection.commit()

    student = models.Student.from_row(
        connection.execute("SELECT * FROM students").fetchone()
    )
    assert student.student_id == "40222"
    assert student.full_name == "علی رضایی"
    assert student.photo_count == 0

    course = models.Course.from_row(
        connection.execute("SELECT * FROM courses").fetchone()
    )
    assert course.title == "کلاس اصلی"

    session = models.Session.from_row(
        connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    )
    assert session.course_id == 1
    assert session.status == "active"
    assert session.late_after_minutes == 10

    record = models.AttendanceRecord.from_row(
        connection.execute("SELECT * FROM attendance").fetchone()
    )
    assert record.session_id == session_id
    assert record.student_id == "40222"
    assert record.source == "manual"
    assert record.confidence is None
