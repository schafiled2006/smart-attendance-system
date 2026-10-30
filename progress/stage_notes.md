# Stage Notes

## Stage 1 - structure, config.py, errors.py, requirements.txt
- Files created or changed: `backend/__init__.py`, `backend/config.py`, `backend/errors.py`, `requirements.txt`, `.gitignore`, `.clinerules`, `check_env.py`, plus folder structure (`backend/`, `known_faces/`, `embeddings/`, `reports/`, `logs/`, `data/`, `tests/`, `progress/`).
- Public functions: `config.get_db_path()`, `errors.AppError(code, message_fa)` base class and subclasses.
- Decisions made: Database path overridable via `ATTENDANCE_DB` env var for tests. `face_recognition` installed with `--no-deps` to avoid rebuilding dlib from source.
- Assumptions and known limitations: Offline-only, CPU-only, `model="hog"` for face recognition.
- Things to revisit or edit later: Lock dependency versions in `requirements.txt` with `pip freeze` (per PROJECT_CONTEXT.md §2).
- Tests: `tests/test_stage1_setup.py`, covers setup/env checks. Skips: none reported.

## Stage 2 - utils.py, database.py, models.py
- Files created or changed: `backend/utils.py`, `backend/database.py`, `backend/models.py`.
- Public functions: `normalize_digits`, `now_tehran`, `to_iso`, `parse_iso`, `to_jalali_str`, `setup_logging`; `get_connection`, `init_db`; dataclasses `Student`, `Course`, `Session`, `AttendanceRecord`.
- Decisions made: `init_db` idempotent, inserts default course "کلاس اصلی" if courses table empty. Every connection uses `PRAGMA foreign_keys=ON` and `row_factory=sqlite3.Row`.
- Assumptions and known limitations: SQLite-only, timezone Asia/Tehran.
- Things to revisit or edit later: None known.
- Tests: `tests/test_stage2_core.py`, covers digit normalization, Tehran time, ISO roundtrip, Jalali formatting, schema, table columns, FK constraints. Skips: none.

## Stage 3 - recognition.py
- Files created or changed: `backend/recognition.py`.
- Public functions: `load_image_rgb`, `encode_single_face`, `reload_embeddings`, `match_encoding`, `recognize_frame`.
- Decisions made: `match_encoding` accepts only if best distance <= FACE_TOLERANCE and margin >= MATCH_MARGIN (margin waived if only one student). `recognize_frame` returns list of {student_id, distance, box}; box normalized 0-1.
- Assumptions and known limitations: Real-photo tests skip if `tests/data/` missing.
- Things to revisit or edit later: None known.
- Tests: `tests/test_stage3_recognition.py`, covers encoding, matching (accept/reject by tolerance/margin), no-students case, frame downscaling, invalid input, unknown faces. Skips: `test_encode_single_face_on_rea` and `test_match_accepts_close_encod` may skip if real photos missing.

## Stage 4 - enrollment.py
- Files created or changed: `backend/enrollment.py`, `tests/test_stage4_enrollment.py`.
- Public functions: `add_student`, `process_photos`, `get_student`, `list_students`, `update_student`, `delete_student`.
- Decisions made: `student_id` whitelist `^[A-Za-z0-9_-]+$` after `normalize_digits`. Photos clipped to `MAX_PHOTOS=5`, minimum `MIN_PHOTOS=3`. Embedding saved as average in `embeddings/<student_id>.npy`. `delete_student` keeps photos, removes `.npy` and DB row; requires `force=True` if attendance exists. Real-photo test rewritten to require zero wrong identifications.
- Assumptions and known limitations: Uses `face_recognition` + `dlib-bin` (CPU only).
- Things to revisit or edit later: None known.
- Tests: `tests/test_stage4_enrollment.py` — 29 tests (27 logical + 1 real photo + 1 skip guard). All pass. Real-photo test `test_real_photos_never_identify_the_wrong_student` PASSED.

## Stage 5 - session_manager.py (+ list_courses)
- Files created or changed: `backend/session_manager.py`, `tests/test_stage5_session.py`.
- Public functions: `start_session(course_id=1, late_after_minutes=None)`, `close_session(session_id=None)`, `get_active_session()`, `get_session(session_id)`, `list_sessions(limit=50)`, `list_courses()`.
- Decisions made: `start_session` validates course exists and `late_after_minutes` in [0, 600] int; raises `SessionAlreadyActiveError` via explicit check and `sqlite3.IntegrityError` from partial unique index. `list_courses` returns all course columns ordered by id. Returned dicts have exactly table columns (no extra display fields). Does not import `attendance_service`. Config read as `config.NAME` at call time. Logs to `logs/app.log`.
- Assumptions and known limitations: Only course_id=1 (default course) exists unless tests insert more via raw SQL.
- Things to revisit or edit later: None known.
- Tests: `tests/test_stage5_session.py` — 22 tests (21 original + 1 list_courses). All pass. Covers start/read/close/start-after-close/duplicate-close/unknown-ids/default-late/invalid-course/invalid-late/list-order-and-limit/get-active-when-none/raw-SQL-unique-index/list_courses.
- pytest.ini decision: `pytest.ini` sets `addopts = --basetemp=.pytest_tmp` to avoid Windows `PermissionError` in the system Temp folder during pytest teardown. This was decided in Stage 5 and must NOT be modified or deleted.

## Stage 6 - attendance_service.py (in progress)
- Files to create or change: `backend/attendance_service.py`, `tests/test_stage6_*.py`.
- Public functions: `log_attendance`, `remove_attendance`, `get_session_attendance`, `get_session_summary`, `process_recognition_result`; `StreakTracker` class + `clear_session_state`.
- Constants: `STATUS_LABELS_FA`, `SOURCE_LABELS_FA`.
- Decisions made: (see Stage 6 implementation notes below)
- Assumptions and known limitations: (see below)
- Things to revisit or edit later: (see below)
- Tests: (to be filled after implementation)