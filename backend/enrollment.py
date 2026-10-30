"""Student enrollment and photo processing.

Stage 4. Business rules live here (see PROJECT_CONTEXT.md sections 7 and 8);
thresholds and paths are always read from ``backend.config`` at call time so
tests can monkeypatch them.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import cv2
import numpy as np

from backend import config, recognition
from backend.database import get_connection
from backend.errors import (
    InvalidInputError,
    NoFaceError,
    NotEnoughPhotosError,
    MultipleFacesError,
    StudentExistsError,
    StudentHasAttendanceError,
    StudentNotFoundError,
)
from backend.models import Student
from backend.utils import normalize_digits, now_tehran, to_iso

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
STUDENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

REASON_NO_FACE = "no_face"
REASON_MULTIPLE_FACES = "multiple_faces"
REASON_UNREADABLE = "unreadable"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _clean_student_id(student_id: str) -> str:
    """Normalize digits and enforce the ASCII whitelist for student ids."""
    if not isinstance(student_id, str):
        raise InvalidInputError("شماره دانشجویی باید متن باشد.")
    cleaned = normalize_digits(student_id).strip()
    if not cleaned:
        raise InvalidInputError("شماره دانشجویی نمی‌تواند خالی باشد.")
    if not STUDENT_ID_PATTERN.match(cleaned):
        raise InvalidInputError(
            "شماره دانشجویی فقط می‌تواند شامل حروف انگلیسی، رقم، خط تیره و زیرخط باشد."
        )
    return cleaned


def _clean_text(value: str, field_fa: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidInputError(f"{field_fa} باید متن باشد.")
    return value.strip()


def _resolve_embedding(embedding_path: str | None) -> Path | None:
    """Resolve a stored ``embedding_path`` (relative to the project root)."""
    if not embedding_path:
        return None
    path = Path(embedding_path)
    return path if path.is_absolute() else config.PROJECT_ROOT / path


def _student_dict(row) -> dict:
    student = Student.from_row(row)
    embedding_path = student.embedding_path
    resolved = _resolve_embedding(embedding_path)
    has_embedding = resolved is not None and resolved.is_file()
    return {
        "student_id": student.student_id,
        "full_name": student.full_name,
        "major": student.major,
        "term": student.term,
        "embedding_path": embedding_path,
        "photo_count": student.photo_count,
        "created_at": student.created_at,
        "has_embedding": has_embedding,
    }


def _fetch_row(student_id: str):
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    finally:
        connection.close()


def _require_row(student_id: str):
    row = _fetch_row(student_id)
    if row is None:
        raise StudentNotFoundError(student_id)
    return row


def _prepare_rgb(path: Path) -> np.ndarray:
    """Load a photo, apply EXIF rotation and downscale its longest side."""
    rgb = recognition.load_image_rgb(path)
    height, width = rgb.shape[:2]
    scale = min(1.0, config.PHOTO_MAX_SIDE / max(width, height))
    if scale < 1.0:
        rgb = cv2.resize(
            rgb,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return rgb


def _photo_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def _existing_embeddings(exclude: str) -> dict[str, np.ndarray]:
    """Load other students' embeddings straight from disk (no cache coupling)."""
    embeddings: dict[str, np.ndarray] = {}
    embeddings_dir = Path(config.EMBEDDINGS_DIR)
    if not embeddings_dir.is_dir():
        return embeddings
    for path in sorted(embeddings_dir.glob("*.npy")):
        if path.stem == exclude:
            continue
        try:
            vector = np.load(path)
        except Exception:  # pragma: no cover - defensive
            continue
        if vector.shape == (128,) and np.isfinite(vector).all():
            embeddings[path.stem] = np.asarray(vector, dtype=np.float64)
    return embeddings


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def add_student(
    student_id: str,
    full_name: str,
    major: str = "",
    term: str = "",
) -> dict:
    """Register a student and create the ``known_faces/<student_id>`` folder."""
    student_id = _clean_student_id(student_id)
    full_name = _clean_text(full_name, "نام و نام خانوادگی")
    if not full_name:
        raise InvalidInputError("نام و نام خانوادگی نمی‌تواند خالی باشد.")
    major = _clean_text(major, "رشته")
    term = _clean_text(term, "ترم")

    if _fetch_row(student_id) is not None:
        raise StudentExistsError(student_id)

    folder = Path(config.KNOWN_FACES_DIR) / student_id
    folder.mkdir(parents=True, exist_ok=True)

    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO students (student_id, full_name, major, term, "
            "embedding_path, photo_count, created_at) VALUES (?, ?, ?, ?, NULL, 0, ?)",
            (student_id, full_name, major, term, to_iso(now_tehran())),
        )
        connection.commit()
    finally:
        connection.close()

    return _student_dict(_require_row(student_id))


def process_photos(student_id: str) -> dict:
    """Build the student's mean embedding from the photos in their folder.

    Returns ``{"accepted": int, "rejected": [{"file", "reason"}],
    "warnings": [...], "embedding_saved": bool}``.

    Raises ``NotEnoughPhotosError`` when fewer than ``MIN_PHOTOS`` photos are
    valid; in that case an existing embedding is never overwritten.
    """
    student_id = _clean_student_id(student_id)
    _require_row(student_id)

    folder = Path(config.KNOWN_FACES_DIR) / student_id
    photos = _photo_files(folder)
    warnings: list[dict] = []

    if len(photos) > config.MAX_PHOTOS:
        warnings.append(
            {
                "code": "photos_clipped",
                "message": (
                    f"تعداد عکس‌ها بیش از حد مجاز است؛ فقط {config.MAX_PHOTOS} "
                    "عکس اول پردازش شد."
                ),
                "total": len(photos),
                "used": config.MAX_PHOTOS,
            }
        )
        photos = photos[: config.MAX_PHOTOS]

    encodings: list[np.ndarray] = []
    rejected: list[dict] = []

    for path in photos:
        try:
            rgb = _prepare_rgb(path)
        except Exception as exc:
            logger.warning("عکس خوانده نشد: %s (%s)", path, exc)
            rejected.append({"file": path.name, "reason": REASON_UNREADABLE})
            continue

        try:
            encoding = recognition.encode_single_face(rgb)
        except MultipleFacesError:
            logger.warning("عکس با چند چهره رد شد: %s", path.name)
            rejected.append({"file": path.name, "reason": REASON_MULTIPLE_FACES})
            continue
        except NoFaceError:
            logger.warning("عکس بدون چهره رد شد: %s", path.name)
            rejected.append({"file": path.name, "reason": REASON_NO_FACE})
            continue

        encodings.append(encoding)

    accepted = len(encodings)
    if accepted < config.MIN_PHOTOS:
        logger.warning(
            "عکس‌های معتبر کافی نیست برای %s: %s از %s",
            student_id,
            accepted,
            config.MIN_PHOTOS,
        )
        error = NotEnoughPhotosError(required=config.MIN_PHOTOS, found=accepted)
        error.accepted = accepted
        error.rejected = rejected
        error.warnings = warnings
        raise error

    mean_embedding = np.mean(np.stack(encodings), axis=0)

    for other_id, other_vector in _existing_embeddings(exclude=student_id).items():
        distance = float(np.linalg.norm(other_vector - mean_embedding))
        if distance < config.FACE_TOLERANCE:
            logger.warning(
                "هشدار شباهت: %s به %s نزدیک است (فاصله %.3f)",
                student_id,
                other_id,
                distance,
            )
            warnings.append(
                {
                    "code": "similar_face",
                    "student_id": other_id,
                    "distance": round(distance, 4),
                    "message": "چهره این دانشجو به دانشجوی دیگری نزدیک است.",
                }
            )

    embeddings_dir = Path(config.EMBEDDINGS_DIR)
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    embedding_file = embeddings_dir / f"{student_id}.npy"
    np.save(embedding_file, mean_embedding)

    try:
        stored_path = embedding_file.resolve().relative_to(
            config.PROJECT_ROOT
        ).as_posix()
    except ValueError:  # embeddings folder outside the project (tests)
        stored_path = str(embedding_file.resolve())

    connection = get_connection()
    try:
        connection.execute(
            "UPDATE students SET embedding_path = ?, photo_count = ? "
            "WHERE student_id = ?",
            (stored_path, accepted, student_id),
        )
        connection.commit()
    finally:
        connection.close()

    recognition.reload_embeddings()

    return {
        "accepted": accepted,
        "rejected": rejected,
        "warnings": warnings,
        "embedding_saved": True,
    }


def get_student(student_id: str) -> dict | None:
    """Return a student as a dict (with ``has_embedding``) or ``None``."""
    student_id = _clean_student_id(student_id)
    row = _fetch_row(student_id)
    return _student_dict(row) if row is not None else None


def list_students() -> list[dict]:
    """Return every student ordered by student_id."""
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM students ORDER BY student_id"
        ).fetchall()
    finally:
        connection.close()
    return [_student_dict(row) for row in rows]


def update_student(
    student_id: str,
    full_name: str | None = None,
    major: str | None = None,
    term: str | None = None,
) -> dict:
    """Update the given metadata fields and return the updated student."""
    student_id = _clean_student_id(student_id)
    _require_row(student_id)

    updates: list[str] = []
    values: list[str] = []
    if full_name is not None:
        cleaned = _clean_text(full_name, "نام و نام خانوادگی")
        if not cleaned:
            raise InvalidInputError("نام و نام خانوادگی نمی‌تواند خالی باشد.")
        updates.append("full_name = ?")
        values.append(cleaned)
    if major is not None:
        updates.append("major = ?")
        values.append(_clean_text(major, "رشته"))
    if term is not None:
        updates.append("term = ?")
        values.append(_clean_text(term, "ترم"))

    if updates:
        values.append(student_id)
        connection = get_connection()
        try:
            connection.execute(
                f"UPDATE students SET {', '.join(updates)} WHERE student_id = ?",
                values,
            )
            connection.commit()
        finally:
            connection.close()

    return _student_dict(_require_row(student_id))


def delete_student(student_id: str, force: bool = False) -> bool:
    """Delete a student, keeping their photo folder.

    Raises ``StudentHasAttendanceError`` when attendance rows exist and
    ``force`` is false. The derived ``.npy`` file is removed and the
    recognition cache is reloaded.
    """
    student_id = _clean_student_id(student_id)
    _require_row(student_id)

    connection = get_connection()
    try:
        attendance_count = connection.execute(
            "SELECT COUNT(*) AS n FROM attendance WHERE student_id = ?",
            (student_id,),
        ).fetchone()["n"]
        if attendance_count and not force:
            raise StudentHasAttendanceError(student_id)

        with connection:
            if attendance_count:
                connection.execute(
                    "DELETE FROM attendance WHERE student_id = ?", (student_id,)
                )
            connection.execute(
                "DELETE FROM students WHERE student_id = ?", (student_id,)
            )
    finally:
        connection.close()

    embedding_file = Path(config.EMBEDDINGS_DIR) / f"{student_id}.npy"
    if embedding_file.is_file():
        try:
            embedding_file.unlink()
        except OSError as exc:  # pragma: no cover - Windows file locks
            logger.warning("حذف فایل embedding ناموفق بود: %s (%s)", embedding_file, exc)

    recognition.reload_embeddings()
    logger.info("دانشجو حذف شد: %s (force=%s)", student_id, force)
    return True
