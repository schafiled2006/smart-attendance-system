"""Non-interactive CLI commands (argparse).

Stage 9. Provides administrative CLI commands for initializing the database,
managing students, processing photos, controlling sessions, generating reports,
and running the API server.

Supports clean ASCII box/table formatting, UTF-8 output on Windows PowerShell 5.1,
and an explicit --lang flag ('en' by default, or 'fa').
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

import jdatetime

from backend import config, database, enrollment, report_service, session_manager
from backend.cli_format import print_box, print_table
from backend.errors import (
    AppError,
    InvalidInputError,
    NotEnoughPhotosError,
    ReportEmptyError,
    SessionNotFoundError,
    StudentExistsError,
    StudentNotFoundError,
)

# Configure output streams for clean UTF-8 on Windows PowerShell
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


ERROR_MESSAGES_EN: dict[str, str] = {
    "student_exists": "Student already exists.",
    "student_not_found": "Student not found.",
    "student_has_attendance": "Student has attendance records and cannot be deleted without --force.",
    "no_face": "No face found in image.",
    "multiple_faces": "Multiple faces found in image.",
    "not_enough_photos": "Not enough valid photos (minimum 3 required).",
    "session_already_active": "Another session is already active.",
    "no_active_session": "No active session found.",
    "session_not_found": "Session not found.",
    "session_closed": "Session is already closed.",
    "invalid_input": "Invalid input provided.",
    "report_empty": "No attendance records found for the requested report.",
    "payload_too_large": "Image payload is too large (maximum 10 MB).",
}


def _format_error(err: AppError, lang: str = "en") -> str:
    """Format AppError with stable code and language-specific text."""
    if lang == "fa":
        return f"خطا [{err.code}]: {err.message_fa}"

    msg = ERROR_MESSAGES_EN.get(err.code, str(err))
    return f"Error [{err.code}]: {msg}"


def _format_bidi_name(name: str) -> str:
    """Shape Persian name for RTL display if arabic_reshaper/bidi are available."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(name))
    except Exception:
        return name


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Smart Attendance System - Administrative CLI",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "fa"],
        default="en",
        help="Output language (default: en)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # 1. init-db
    subparsers.add_parser("init-db", help="Initialize database schema and default course")

    # 2. add-student
    p_add = subparsers.add_parser("add-student", help="Register student metadata")
    p_add.add_argument("--id", required=True, help="Unique student ID")
    p_add.add_argument("--name", required=True, help="Full name")
    p_add.add_argument("--major", default="", help="Academic major (optional)")
    p_add.add_argument("--term", default="", help="Academic term (optional)")

    # 3. delete-student
    p_del = subparsers.add_parser("delete-student", help="Delete a student record")
    p_del.add_argument("--id", required=True, help="Student ID to delete")
    p_del.add_argument(
        "--force",
        action="store_true",
        help="Force deletion even if student has attendance records",
    )

    # 4. process-photos
    p_photos = subparsers.add_parser("process-photos", help="Process photos and compute mean embedding")
    p_photos.add_argument("--id", required=True, help="Student ID")

    # 5. list-students
    p_list = subparsers.add_parser("list-students", help="List all registered students")
    p_list.add_argument(
        "--show-names",
        action="store_true",
        help="Print Persian full names in a separate section below the ASCII table",
    )

    # 6. start-session
    p_start = subparsers.add_parser("start-session", help="Start a new attendance session")
    p_start.add_argument("--course-id", type=int, default=1, help="Course ID (default: 1)")
    p_start.add_argument(
        "--late-after",
        type=int,
        default=None,
        help="Late threshold in minutes (default: 10)",
    )

    # 7. close-session
    p_close = subparsers.add_parser("close-session", help="Close an attendance session")
    p_close.add_argument(
        "--id",
        type=int,
        default=None,
        help="Session ID to close (defaults to currently active session)",
    )

    # 8. report
    p_report = subparsers.add_parser("report", help="Export Excel attendance report")
    r_group = p_report.add_mutually_exclusive_group(required=True)
    r_group.add_argument("--session-id", type=int, help="Single session ID to export")
    r_group.add_argument(
        "--daily",
        action="store_true",
        help="Export all sessions for a given date into a multi-sheet Excel file",
    )
    p_report.add_argument(
        "--date",
        default=None,
        help="Shamsi date for daily report (format: 1403-08-11 or 1403/08/11; default: today)",
    )

    # 9. run
    p_run = subparsers.add_parser("run", help="Run FastAPI server via uvicorn")
    p_run.add_argument("--host", default=None, help="Server host (default: 127.0.0.1)")
    p_run.add_argument("--port", type=int, default=None, help="Server port (default: 8000)")

    return parser


def _handle_init_db(lang: str) -> int:
    database.init_db()
    if lang == "fa":
        print_box(
            "مقداردهی اولیه پایگاه داده",
            [
                ("وضعیت", "موفقیت‌آمیز"),
                ("درس پیش‌فرض", "درس شماره ۱ ایجاد شد"),
            ],
        )
    else:
        print_box(
            "Database initialized",
            [
                ("Status", "Success"),
                ("Default item", "Course #1 ready"),
            ],
        )
    return 0


def _handle_add_student(args: argparse.Namespace) -> int:
    try:
        student = enrollment.add_student(
            student_id=args.id,
            full_name=args.name,
            major=args.major,
            term=args.term,
        )
        if args.lang == "fa":
            print_box(
                "ثبت دانشجو",
                [
                    ("شماره دانشجویی", student["student_id"]),
                    ("نام و نام خانوادگی", student["full_name"]),
                    ("رشته", student["major"] or "-"),
                    ("ترم", student["term"] or "-"),
                ],
            )
        else:
            print_box(
                "Student registered",
                [
                    ("Student ID", student["student_id"]),
                    ("Full Name", student["full_name"]),
                    ("Major", student["major"] or "-"),
                    ("Term", student["term"] or "-"),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_delete_student(args: argparse.Namespace) -> int:
    try:
        enrollment.delete_student(student_id=args.id, force=args.force)
        if args.lang == "fa":
            print_box(
                "حذف دانشجو",
                [
                    ("شماره دانشجویی", args.id),
                    ("اجباری (Force)", "بله" if args.force else "خیر"),
                    ("وضعیت", "با موفقیت حذف شد"),
                ],
            )
        else:
            print_box(
                "Student deleted",
                [
                    ("Student ID", args.id),
                    ("Force", str(args.force)),
                    ("Status", "Successfully removed"),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_process_photos(args: argparse.Namespace) -> int:
    try:
        res = enrollment.process_photos(student_id=args.id)
        saved = "Saved" if res.get("embedding_saved") else "Failed"
        saved_fa = "ذخیره شد" if res.get("embedding_saved") else "ناموفق"
        if args.lang == "fa":
            print_box(
                "پردازش تصاویر",
                [
                    ("شماره دانشجویی", args.id),
                    ("پذیرفته‌شده", res["accepted"]),
                    ("ردشده", len(res["rejected"])),
                    ("امبدینگ", saved_fa),
                ],
            )
        else:
            print_box(
                "Photos processed",
                [
                    ("Student ID", args.id),
                    ("Accepted", res["accepted"]),
                    ("Rejected", len(res["rejected"])),
                    ("Embedding", saved),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_list_students(args: argparse.Namespace) -> int:
    students = enrollment.list_students()
    if not students:
        if args.lang == "fa":
            print("هیچ دانشجویی در سیستم ثبت نشده است.")
        else:
            print("No students found in the database.")
        return 0

    if args.lang == "fa":
        headers = ["شناسه", "رشته", "ترم", "عکس‌ها", "امبدینگ"]
        rows = [
            [
                s["student_id"],
                s.get("major") or "-",
                s.get("term") or "-",
                s.get("photo_count", 0),
                "دارد" if s.get("has_embedding") else "ندارد",
            ]
            for s in students
        ]
        print_table(headers, rows)
        print("\nاسامی دانشجویان:")
        for s in students:
            print(f"  {s['student_id']}: {_format_bidi_name(s['full_name'])}")
    else:
        headers = ["Student ID", "Major", "Term", "Photos", "Embedding"]
        rows = [
            [
                s["student_id"],
                s.get("major") or "-",
                s.get("term") or "-",
                s.get("photo_count", 0),
                "Yes" if s.get("has_embedding") else "No",
            ]
            for s in students
        ]
        print_table(headers, rows)

        if args.show_names:
            print("\nNames (Persian):")
            for s in students:
                print(f"  {s['student_id']}: {_format_bidi_name(s['full_name'])}")

    return 0


def _handle_start_session(args: argparse.Namespace) -> int:
    try:
        session = session_manager.start_session(
            course_id=args.course_id,
            late_after_minutes=args.late_after,
        )
        if args.lang == "fa":
            print_box(
                "شروع جلسه",
                [
                    ("شناسه جلسه", session["id"]),
                    ("شناسه درس", session["course_id"]),
                    ("حد تأخیر", f"{session['late_after_minutes']} دقیقه"),
                    ("زمان شروع", session["started_at"]),
                ],
            )
        else:
            print_box(
                "Session started",
                [
                    ("Session ID", session["id"]),
                    ("Course ID", session["course_id"]),
                    ("Late after", f"{session['late_after_minutes']} min"),
                    ("Started at", session["started_at"]),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_close_session(args: argparse.Namespace) -> int:
    try:
        session = session_manager.close_session(session_id=args.id)
        if args.lang == "fa":
            print_box(
                "پایان جلسه",
                [
                    ("شناسه جلسه", session["id"]),
                    ("زمان شروع", session["started_at"]),
                    ("زمان پایان", session["ended_at"]),
                    ("وضعیت", session["status"]),
                ],
            )
        else:
            print_box(
                "Session closed",
                [
                    ("Session ID", session["id"]),
                    ("Started at", session["started_at"]),
                    ("Ended at", session["ended_at"]),
                    ("Status", session["status"]),
                ],
            )
        return 0
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_report(args: argparse.Namespace) -> int:
    try:
        if args.session_id is not None:
            path = report_service.export_session_report(session_id=args.session_id)
            if args.lang == "fa":
                print_box(
                    "صدور گزارش جلسه",
                    [
                        ("شناسه جلسه", args.session_id),
                        ("مسیر فایل", str(path)),
                    ],
                )
            else:
                print_box(
                    "Session report exported",
                    [
                        ("Session ID", args.session_id),
                        ("File path", str(path)),
                    ],
                )
            return 0

        # args.daily
        if args.date:
            cleaned = args.date.strip().replace("/", "-")
            parts = cleaned.split("-")
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                err_msg = (
                    "خطا: فرمت تاریخ شمسی نامعتبر است. نمونه: 1403-08-11"
                    if args.lang == "fa"
                    else "Error [invalid_input]: Invalid Shamsi date format. Example: 1403-08-11"
                )
                print(err_msg, file=sys.stderr)
                return 1
            try:
                jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
                j_date = jdatetime.date(jy, jm, jd)
                g_date_iso = j_date.togregorian().isoformat()
            except Exception:
                err_msg = (
                    "خطا: تاریخ شمسی واردشده نامعتبر است."
                    if args.lang == "fa"
                    else "Error [invalid_input]: Invalid Shamsi calendar date."
                )
                print(err_msg, file=sys.stderr)
                return 1
        else:
            j_today = jdatetime.date.today()
            g_date_iso = j_today.togregorian().isoformat()

        path = report_service.export_daily_report(date_iso=g_date_iso)
        if args.lang == "fa":
            print_box(
                "صدور گزارش روزانه",
                [
                    ("تاریخ میلادی", g_date_iso),
                    ("مسیر فایل", str(path)),
                ],
            )
        else:
            print_box(
                "Daily report exported",
                [
                    ("Date (Gregorian)", g_date_iso),
                    ("File path", str(path)),
                ],
            )
        return 0
    except ReportEmptyError:
        err_msg = (
            "خطا [report_empty]: هیچ جلسه‌ای برای صدور گزارش در این تاریخ یافت نشد."
            if args.lang == "fa"
            else "Error [report_empty]: No sessions found for the requested date."
        )
        print(err_msg, file=sys.stderr)
        return 1
    except AppError as err:
        print(_format_error(err, args.lang), file=sys.stderr)
        return 1


def _handle_run(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:  # pragma: no cover
        err_msg = (
            "خطا: ماژول uvicorn نصب نیست."
            if args.lang == "fa"
            else "Error: uvicorn module is not installed."
        )
        print(err_msg, file=sys.stderr)
        return 1

    host = args.host or config.API_HOST
    port = args.port or config.API_PORT
    uvicorn.run("backend.api.app:app", host=host, port=port, workers=1, reload=False)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    handlers = {
        "init-db": lambda: _handle_init_db(args.lang),
        "add-student": lambda: _handle_add_student(args),
        "delete-student": lambda: _handle_delete_student(args),
        "process-photos": lambda: _handle_process_photos(args),
        "list-students": lambda: _handle_list_students(args),
        "start-session": lambda: _handle_start_session(args),
        "close-session": lambda: _handle_close_session(args),
        "report": lambda: _handle_report(args),
        "run": lambda: _handle_run(args),
    }

    handler = handlers.get(args.subcommand)
    if handler:
        return handler()
    return 1  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
