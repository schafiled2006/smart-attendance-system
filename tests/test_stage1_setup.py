"""Stage 1 tests: project skeleton, config, errors and environment."""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

from backend import config
from backend import errors

REQUIRED_MODULES = [
    "cv2",
    "numpy",
    "PIL",
    "dlib",
    "face_recognition",
    "face_recognition_models",
    "click",
    "openpyxl",
    "jdatetime",
    "tzdata",
    "fastapi",
    "uvicorn",
    "python_multipart",
    "pytest",
    "httpx",
]

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def test_python_version() -> None:
    assert sys.version_info[:2] == (3, 11)


@pytest.mark.parametrize("module_name", REQUIRED_MODULES)
def test_required_module_imports(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None


def test_numpy_is_below_two() -> None:
    numpy = importlib.import_module("numpy")
    assert int(numpy.__version__.split(".")[0]) < 2


def test_config_values() -> None:
    assert config.FACE_TOLERANCE == pytest.approx(0.55)
    assert 0.5 <= config.FACE_TOLERANCE <= 0.6
    assert config.MATCH_MARGIN == pytest.approx(0.05)
    assert config.MIN_PHOTOS == 3
    assert config.MAX_PHOTOS == 5
    assert config.REQUIRED_CONSECUTIVE_FRAMES == 3
    assert config.DEFAULT_LATE_AFTER_MINUTES == 10
    assert config.DETECTION_MODEL == "hog"
    assert config.FRAME_MAX_WIDTH == 640
    assert config.PHOTO_MAX_SIDE == 1280
    assert config.TIMEZONE == "Asia/Tehran"
    assert config.CAMERA_SOURCE == 0
    assert config.PROCESS_EVERY_N_FRAMES == 3
    assert config.API_HOST == "127.0.0.1"
    assert config.API_PORT == 8000
    assert config.CORS_ORIGINS == ["http://localhost:5173"]


def test_config_paths_point_inside_project() -> None:
    root = config.PROJECT_ROOT
    assert root.is_dir()
    for directory in (
        config.KNOWN_FACES_DIR,
        config.EMBEDDINGS_DIR,
        config.REPORTS_DIR,
        config.LOGS_DIR,
        config.DATA_DIR,
    ):
        assert directory.is_dir()
        assert directory.parent == root
    assert config.LOG_FILE == config.LOGS_DIR / "app.log"


def test_database_path_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    expected = (tmp_path / "test_attendance.db").resolve()
    monkeypatch.setenv("ATTENDANCE_DB", str(expected))
    reloaded = importlib.reload(config)
    try:
        assert reloaded.DB_PATH == expected
    finally:
        monkeypatch.delenv("ATTENDANCE_DB", raising=False)
        importlib.reload(config)


def test_database_path_default() -> None:
    assert config.DB_PATH == (config.DATA_DIR / "attendance.db")


def test_get_db_path_reads_env_at_call_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Contract (section 4): get_db_path() must honor ATTENDANCE_DB at call
    time, without any importlib.reload or module re-import."""
    expected = (tmp_path / "late_override.db").resolve()

    monkeypatch.setenv("ATTENDANCE_DB", str(expected))
    assert config.get_db_path() == expected

    monkeypatch.delenv("ATTENDANCE_DB")
    assert config.get_db_path() == (config.DATA_DIR / "attendance.db")


def test_error_hierarchy_and_codes() -> None:
    expected = {
        errors.StudentExistsError: "student_exists",
        errors.StudentNotFoundError: "student_not_found",
        errors.StudentHasAttendanceError: "student_has_attendance",
        errors.NoFaceError: "no_face",
        errors.MultipleFacesError: "multiple_faces",
        errors.NotEnoughPhotosError: "not_enough_photos",
        errors.SessionAlreadyActiveError: "session_already_active",
        errors.NoActiveSessionError: "no_active_session",
        errors.SessionNotFoundError: "session_not_found",
        errors.SessionClosedError: "session_closed",
        errors.InvalidInputError: "invalid_input",
        errors.ReportEmptyError: "report_empty",
    }
    for error_class, code in expected.items():
        assert issubclass(error_class, errors.AppError)
        instance = error_class()
        assert instance.code == code
        assert instance.message_fa
        assert instance.to_dict() == {"error": code, "message": instance.message_fa}


def test_base_error_signature() -> None:
    error = errors.AppError("custom", "پیام سفارشی")
    assert error.code == "custom"
    assert error.message_fa == "پیام سفارشی"
    assert str(error) == "پیام سفارشی"


def test_stage_one_files_exist() -> None:
    root = config.PROJECT_ROOT
    for relative in (
        "PROJECT_CONTEXT.md",
        ".clinerules",
        ".gitignore",
        "requirements.txt",
        "check_env.py",
        "manage.py",
        "main_test.py",
        "README.md",
        "backend/__init__.py",
        "backend/config.py",
        "backend/errors.py",
        "backend/utils.py",
        "backend/models.py",
        "backend/database.py",
        "backend/recognition.py",
        "backend/enrollment.py",
        "backend/session_manager.py",
        "backend/attendance_service.py",
        "backend/report_service.py",
        "backend/api/__init__.py",
        "backend/api/app.py",
        "backend/api/schemas.py",
        "progress/current_status.md",
    ):
        assert (root / relative).is_file(), relative


def test_check_env_script_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, "check_env.py"],
        cwd=config.PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(
    not any(
        path.suffix.lower() in IMAGE_SUFFIXES
        for path in (config.PROJECT_ROOT / "tests" / "data").glob("*")
    ),
    reason="no real test image in tests/data/",
)
def test_face_encodings_on_sample_image() -> None:
    import face_recognition
    import numpy as np
    from PIL import Image, ImageOps

    path = next(
        path
        for path in sorted((config.PROJECT_ROOT / "tests" / "data").glob("*"))
        if path.suffix.lower() in IMAGE_SUFFIXES
    )
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((config.PHOTO_MAX_SIDE, config.PHOTO_MAX_SIDE))
        rgb = np.array(image)

    locations = face_recognition.face_locations(rgb, model=config.DETECTION_MODEL)
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    assert encodings
    assert encodings[0].shape == (128,)
# TEMP FILE FOR STAGE 6
pass