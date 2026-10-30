"""Face encoding, embedding caching and matching.

Implemented in stage 3. All thresholds come from ``backend.config`` so tests
can monkeypatch them; embeddings are loaded from ``config.EMBEDDINGS_DIR``
(overridden to temporary directories in tests).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageOps

from backend import config
from backend.errors import InvalidInputError, MultipleFacesError, NoFaceError

logger = logging.getLogger(__name__)

# ``None`` means the cache has not been loaded yet; {} means loaded and empty.
_EMBEDDINGS: dict[str, np.ndarray] | None = None


def load_image_rgb(path: str | os.PathLike) -> np.ndarray:
    """Load an image file as an RGB ``np.ndarray``, honouring EXIF rotation."""
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        return np.asarray(image)


def encode_single_face(rgb: np.ndarray) -> np.ndarray:
    """Return the 128-d encoding of the single face in ``rgb``.

    Raises ``NoFaceError`` when no face is found and ``MultipleFacesError``
    when more than one face is present.
    """
    rgb = np.asarray(rgb)
    locations = face_recognition.face_locations(rgb, model=config.DETECTION_MODEL)
    if not locations:
        raise NoFaceError()
    if len(locations) > 1:
        raise MultipleFacesError(f"تعداد چهره‌های شناسایی‌شده: {len(locations)}")
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    if not encodings:  # pragma: no cover - defensive, should not happen
        raise NoFaceError("چهره مکان‌یابی شد اما استخراج انکودینگ ناموفق بود")
    return np.asarray(encodings[0], dtype=np.float64)


def reload_embeddings() -> int:
    """(Re)load every ``<student_id>.npy`` stored in the embeddings folder.

    Invalid files (unreadable or not 128-d) are skipped with a warning.
    Returns the number of students loaded.
    """
    global _EMBEDDINGS
    embeddings: dict[str, np.ndarray] = {}
    embeddings_dir = Path(config.EMBEDDINGS_DIR)
    if embeddings_dir.is_dir():
        for path in sorted(embeddings_dir.glob("*.npy")):
            try:
                vector = np.load(path)
            except Exception as exc:
                logger.warning("خواندن embedding ناموفق بود: %s (%s)", path.name, exc)
                continue
            if vector.shape != (128,) or not np.isfinite(vector).all():
                logger.warning(
                    "embedding نامعتبر (ابعاد %s) نادیده گرفته شد: %s",
                    tuple(vector.shape),
                    path.name,
                )
                continue
            embeddings[path.stem] = np.asarray(vector, dtype=np.float64)
    _EMBEDDINGS = embeddings
    return len(_EMBEDDINGS)


def match_encoding(enc: np.ndarray) -> tuple[str | None, float]:
    """Match ``enc`` against the cached embeddings (pure, testable logic).

    Returns ``(student_id, best_distance)``. ``student_id`` is ``None`` when
    the encoding matches nobody, when the best distance exceeds
    ``FACE_TOLERANCE``, or when the second-nearest student is closer than
    ``MATCH_MARGIN`` to the best one (ambiguous). With a single enrolled
    student the margin rule is skipped; with no students at all the result is
    ``(None, inf)``.
    """
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        reload_embeddings()

    if not _EMBEDDINGS:
        return None, float("inf")

    enc = np.asarray(enc, dtype=np.float64)
    distances = {
        student_id: float(np.linalg.norm(vector - enc))
        for student_id, vector in _EMBEDDINGS.items()
    }
    best_id, best = min(distances.items(), key=lambda item: item[1])

    if best > config.FACE_TOLERANCE:
        return None, best

    if len(distances) > 1:
        second = min(d for sid, d in distances.items() if sid != best_id)
        if second < best + config.MATCH_MARGIN:
            return None, best

    return best_id, best


def recognize_frame(bgr: np.ndarray) -> list[dict]:
    """Detect and identify every face in a BGR video frame.

    Wide frames are downscaled so their width does not exceed
    ``FRAME_MAX_WIDTH`` before detection. Returns one dict per face:
    ``{"student_id": str | None, "distance": float, "box": (top, right, bottom, left)}``
    where box coordinates are relative to the original frame (0 to 1).
    """
    bgr = np.asarray(bgr)
    if bgr.ndim == 2:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_GRAY2BGR)
    elif bgr.ndim == 3 and bgr.shape[2] == 4:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_BGRA2BGR)
    elif bgr.ndim == 3 and bgr.shape[2] != 3:
        raise InvalidInputError("تعداد کانال‌های تصویر نامعتبر است.")
    height, width = bgr.shape[:2]
    scale = min(1.0, config.FRAME_MAX_WIDTH / width)
    if scale < 1.0:
        small = cv2.resize(
            bgr,
            (max(1, round(width * scale)), max(1, round(height * scale))),
        )
    else:
        small = bgr

    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model=config.DETECTION_MODEL)
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)

    results: list[dict] = []
    for (top, right, bottom, left), enc in zip(locations, encodings):
        student_id, distance = match_encoding(enc)
        if student_id is None:
            logger.info("چهره ناشناس دیده شد (نزدیک‌ترین فاصله: %.3f)", distance)
        results.append(
            {
                "student_id": student_id,
                "distance": distance,
                "box": (top / height, right / width, bottom / height, left / width),
            }
        )
    return results
