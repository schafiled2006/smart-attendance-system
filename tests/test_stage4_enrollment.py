"""Stage 4 tests: enrollment.py.

Logic tests use synthetic images and a temporary database; real-photo tests
read ``tests/data/students/<student_id>/*.jpg`` and are skipped when that
folder is missing. Originals are never modified: photos are copied into a
temporary ``known_faces`` folder.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

from backend import config, database, enrollment, recognition
from backend.errors import (
    InvalidInputError,
    NotEnoughPhotosError,
    StudentExistsError,
    StudentHasAttendanceError,
    StudentNotFoundError,
)
from backend.utils import now_tehran, to_iso

REAL_PHOTOS_ROOT = config.PROJECT_ROOT / "tests" / "data" / "students"


def _real_student_dirs() -> list[Path]:
    if not REAL_PHOTOS_ROOT.is_dir():
        return []
    return sorted(path for path in REAL_PHOTOS_ROOT.iterdir() if path.is_dir())


REAL_STUDENT_DIRS = _real_student_dirs()
requires_real_photos = pytest.mark.skipif(
    not REAL_STUDENT_DIRS, reason="tests/data/students/ missing"
)


@pytest.fixture()
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate DB, known_faces and embeddings from the real project folders."""
    monkeypatch.setenv("ATTENDANCE_DB", str(tmp_path / "stage4_test.db"))
    known_faces = tmp_path / "known_faces"
    embeddings = tmp_path / "embeddings"
    known_faces.mkdir()
    embeddings.mkdir()
    monkeypatch.setattr(config, "KNOWN_FACES_DIR", known_faces)
    monkeypatch.setattr(config, "EMBEDDINGS_DIR", embeddings)
    database.init_db()
    recognition._EMBEDDINGS = None
    yield {"known_faces": known_faces, "embeddings": embeddings, "tmp": tmp_path}
    recognition._EMBEDDINGS = None


def _write_color_photo(path: Path, color: tuple[int, int, int] = (10, 20, 30)) -> Path:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (60, 60), color=color).save(path)
    return path


def _fake_encode(monkeypatch: pytest.MonkeyPatch, mapping) -> None:
    """Patch encode_single_face with a per-file lookup.

    ``mapping`` maps a photo file name to either a vector or an exception
    instance to raise.
    """

    def fake(rgb):
        name = fake.current_name
        value = mapping[name]
        if isinstance(value, Exception):
            raise value
        return value

    fake.current_name = ""

    real_loader = recognition.load_image_rgb

    def tagged_loader(path):
        fake.current_name = Path(path).name
        return real_loader(path)

    monkeypatch.setattr(recognition, "load_image_rgb", tagged_loader)
    monkeypatch.setattr(recognition, "encode_single_face", fake)


def _vector(index: int, value: float = 0.5) -> np.ndarray:
    vector = np.zeros(128)
    vector[index] = value
    return vector


def _photo_embedding(student_id: str) -> np.ndarray:
    embeddings_dir = Path(config.EMBEDDINGS_DIR)
    return np.load(embeddings_dir / f"{student_id}.npy")


# --------------------------------------------------------------------------- #
# add_student
# --------------------------------------------------------------------------- #
def test_add_student_creates_row_and_photo_folder(env) -> None:
    result = enrollment.add_student("40123001", " علی رضایی ", "کامپیوتر", "۹۰")

    assert result["student_id"] == "40123001"
    assert result["full_name"] == "علی رضایی"
    assert result["major"] == "کامپیوتر"
    # Section 6 normalizes digits for student ids only, not for term.
    assert result["term"] == "۹۰"
    assert result["photo_count"] == 0
    assert result["has_embedding"] is False
    assert (env["known_faces"] / "40123001").is_dir()
    assert enrollment.get_student("40123001")["full_name"] == "علی رضایی"


def test_add_student_normalizes_persian_and_arabic_digits(env) -> None:
    enrollment.add_student("۴۰۱۲۳۰۰۲", "دانشجو")
    assert enrollment.get_student("40123002") is not None


def test_add_student_duplicate_raises(env) -> None:
    enrollment.add_student("40123001", "اول")
    with pytest.raises(StudentExistsError):
        enrollment.add_student("40123001", "دوم")


@pytest.mark.parametrize("bad_id", ["", "   ", "4012 3001", "4012/3001", "ab.c"])
def test_add_student_rejects_invalid_student_id(env, bad_id: str) -> None:
    with pytest.raises(InvalidInputError):
        enrollment.add_student(bad_id, "نام")


def test_add_student_requires_full_name(env) -> None:
    with pytest.raises(InvalidInputError):
        enrollment.add_student("40123001", "   ")


# --------------------------------------------------------------------------- #
# get / list / update
# --------------------------------------------------------------------------- #
def test_get_student_missing_returns_none(env) -> None:
    assert enrollment.get_student("99999999") is None


def test_get_student_invalid_id_raises(env) -> None:
    with pytest.raises(InvalidInputError):
        enrollment.get_student("bad/id")


def test_update_student_partial_fields(env) -> None:
    enrollment.add_student("40123001", "نام اول", "رشته اول", "1")

    updated = enrollment.update_student("40123001", major="رشته دوم")

    assert updated["full_name"] == "نام اول"
    assert updated["major"] == "رشته دوم"
    assert updated["term"] == "1"


def test_update_student_missing_raises(env) -> None:
    with pytest.raises(StudentNotFoundError):
        enrollment.update_student("40123001", full_name="x")


def test_update_student_rejects_blank_full_name(env) -> None:
    enrollment.add_student("40123001", "نام")
    with pytest.raises(InvalidInputError):
        enrollment.update_student("40123001", full_name="  ")


def test_list_students_sorted_with_has_embedding(env) -> None:
    enrollment.add_student("40123002", "دوم")
    enrollment.add_student("40123001", "اول")

    students = enrollment.list_students()

    assert [s["student_id"] for s in students] == ["40123001", "40123002"]
    assert all(s["has_embedding"] is False for s in students)


# --------------------------------------------------------------------------- #
# process_photos (synthetic)
# --------------------------------------------------------------------------- #
def test_process_photos_averages_accepted_encodings(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(3):
        _write_color_photo(folder / f"{index}.jpg", (index * 40, 10, 10))
    _fake_encode(
        monkeypatch,
        {
            "0.jpg": _vector(0, 0.6),
            "1.jpg": _vector(0, 0.4),
            "2.jpg": _vector(0, 0.5),
        },
    )

    result = enrollment.process_photos("40123001")

    assert result["accepted"] == 3
    assert result["rejected"] == []
    assert result["embedding_saved"] is True
    saved = _photo_embedding("40123001")
    assert saved.shape == (128,)
    assert saved[0] == pytest.approx(0.5)
    stored = enrollment.get_student("40123001")
    assert stored["has_embedding"] is True
    assert stored["photo_count"] == 3


def test_process_photos_reports_rejections_with_reasons(env, monkeypatch) -> None:
    from backend.errors import MultipleFacesError, NoFaceError

    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for name in ("ok.jpg", "noface.jpg", "many.jpg"):
        _write_color_photo(folder / name)
    _fake_encode(
        monkeypatch,
        {
            "ok.jpg": _vector(0),
            "noface.jpg": NoFaceError(),
            "many.jpg": MultipleFacesError("۲ چهره"),
        },
    )

    with pytest.raises(NotEnoughPhotosError) as excinfo:
        enrollment.process_photos("40123001")

    assert excinfo.value.code == "not_enough_photos"
    assert excinfo.value.accepted == 1
    reasons = {item["file"]: item["reason"] for item in excinfo.value.rejected}
    assert reasons == {"noface.jpg": "no_face", "many.jpg": "multiple_faces"}


def test_process_photos_unreadable_file_is_reported(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(3):
        _write_color_photo(folder / f"ok{index}.jpg")
    (folder / "broken.jpg").write_bytes(b"not an image")
    _fake_encode(monkeypatch, {f"ok{i}.jpg": _vector(i, 0.3) for i in range(3)})

    result = enrollment.process_photos("40123001")

    assert result["accepted"] == 3
    assert result["rejected"] == [{"file": "broken.jpg", "reason": "unreadable"}]


def test_process_photos_requires_minimum_valid_photos(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(2):
        _write_color_photo(folder / f"{index}.jpg")
    _fake_encode(monkeypatch, {f"{i}.jpg": _vector(i) for i in range(2)})

    with pytest.raises(NotEnoughPhotosError):
        enrollment.process_photos("40123001")

    assert enrollment.get_student("40123001")["has_embedding"] is False
    assert not (env["embeddings"] / "40123001.npy").exists()


def test_process_photos_does_not_overwrite_existing_embedding(
    env, monkeypatch
) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(3):
        _write_color_photo(folder / f"good{index}.jpg")
    _fake_encode(monkeypatch, {f"good{i}.jpg": _vector(i, 0.5) for i in range(3)})
    enrollment.process_photos("40123001")
    before = _photo_embedding("40123001").copy()

    for path in folder.iterdir():
        path.unlink()
    _write_color_photo(folder / "only.jpg")
    _fake_encode(monkeypatch, {"only.jpg": _vector(9, 0.9)})

    with pytest.raises(NotEnoughPhotosError):
        enrollment.process_photos("40123001")

    after = _photo_embedding("40123001")
    assert np.array_equal(before, after)


def test_process_photos_clips_to_max_photos(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(7):
        _write_color_photo(folder / f"{index:02d}.jpg")
    _fake_encode(
        monkeypatch,
        {f"{i:02d}.jpg": _vector(0, 0.1 * (i + 1)) for i in range(7)},
    )

    result = enrollment.process_photos("40123001")

    assert result["accepted"] == config.MAX_PHOTOS
    assert any(w["code"] == "photos_clipped" for w in result["warnings"])
    assert result["rejected"] == []


def test_process_photos_ignores_non_image_files(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(3):
        _write_color_photo(folder / f"{index}.jpg")
    (folder / "notes.txt").write_text("hello", encoding="utf-8")
    _fake_encode(monkeypatch, {f"{i}.jpg": _vector(i, 0.4) for i in range(3)})

    result = enrollment.process_photos("40123001")

    assert result["accepted"] == 3
    assert result["rejected"] == []


def test_process_photos_warns_on_similar_face(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "اول")
    enrollment.add_student("40123002", "دوم")
    np.save(env["embeddings"] / "40123002.npy", _vector(0, 0.5))

    folder = env["known_faces"] / "40123001"
    for index in range(3):
        _write_color_photo(folder / f"{index}.jpg")
    _fake_encode(monkeypatch, {f"{i}.jpg": _vector(0, 0.5001) for i in range(3)})

    result = enrollment.process_photos("40123001")

    similar = [w for w in result["warnings"] if w["code"] == "similar_face"]
    assert similar and similar[0]["student_id"] == "40123002"
    assert similar[0]["distance"] < config.FACE_TOLERANCE
    assert result["embedding_saved"] is True  # warning must not block saving


def test_process_photos_reloads_recognition_cache(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(3):
        _write_color_photo(folder / f"{index}.jpg")
    _fake_encode(monkeypatch, {f"{i}.jpg": _vector(0, 0.5) for i in range(3)})

    calls: list[int] = []
    real_reload = recognition.reload_embeddings

    def counting_reload():
        calls.append(1)
        return real_reload()

    monkeypatch.setattr(recognition, "reload_embeddings", counting_reload)

    enrollment.process_photos("40123001")

    assert calls, "process_photos must refresh the recognition cache"
    student_id, distance = recognition.match_encoding(_vector(0, 0.5))
    assert student_id == "40123001"
    assert distance == pytest.approx(0.0)


def test_process_photos_missing_student_raises(env) -> None:
    with pytest.raises(StudentNotFoundError):
        enrollment.process_photos("40123001")


# --------------------------------------------------------------------------- #
# delete_student
# --------------------------------------------------------------------------- #
def test_delete_student_removes_row_but_keeps_photos(env, monkeypatch) -> None:
    enrollment.add_student("40123001", "تست")
    folder = env["known_faces"] / "40123001"
    for index in range(3):
        _write_color_photo(folder / f"{index}.jpg")
    _fake_encode(monkeypatch, {f"{i}.jpg": _vector(i, 0.5) for i in range(3)})
    enrollment.process_photos("40123001")

    assert enrollment.delete_student("40123001") is True

    assert enrollment.get_student("40123001") is None
    assert not (env["embeddings"] / "40123001.npy").exists()
    assert folder.is_dir()
    assert len(list(folder.glob("*.jpg"))) == 3


def test_delete_student_with_attendance_requires_force(env) -> None:
    enrollment.add_student("40123001", "تست")
    connection = database.get_connection()
    try:
        connection.execute(
            "INSERT INTO sessions (course_id, started_at, late_after_minutes, status) "
            "VALUES (1, ?, 10, 'closed')",
            (to_iso(now_tehran()),),
        )
        session_id = connection.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]
        connection.execute(
            "INSERT INTO attendance (session_id, student_id, checked_at, source) "
            "VALUES (?, ?, ?, 'manual')",
            (session_id, "40123001", to_iso(now_tehran())),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(StudentHasAttendanceError):
        enrollment.delete_student("40123001")

    assert enrollment.delete_student("40123001", force=True) is True
    assert enrollment.get_student("40123001") is None


def test_delete_student_missing_raises(env) -> None:
    with pytest.raises(StudentNotFoundError):
        enrollment.delete_student("40123001")


# --------------------------------------------------------------------------- #
# Real photos
# --------------------------------------------------------------------------- #
def _copy_real_photos(source: Path, target_root: Path) -> None:
    destination = target_root / source.name
    destination.mkdir(parents=True, exist_ok=True)
    for photo in sorted(source.iterdir()):
        if photo.suffix.lower() in (".jpg", ".jpeg", ".png"):
            shutil.copy2(photo, destination / photo.name)


@requires_real_photos
def test_real_photos_never_identify_the_wrong_student(env) -> None:
    """An unseen photo must resolve to the right student, or be rejected.

    Misidentification is the failure that matters: registering the wrong
    person's attendance. Distance between centroids is only a proxy for that,
    so this test measures the behaviour the camera actually triggers
    (leave-one-out: match each photo against centroids built from the others).

    Passing requires: zero wrong identifications, every student self-matching,
    and a high enough recognition rate that "reject everything" cannot pass.
    """
    photos: dict[str, list[tuple[str, np.ndarray]]] = {}
    report: list[str] = []

    for source in REAL_STUDENT_DIRS:
        _copy_real_photos(source, env["known_faces"])
        enrollment.add_student(source.name, f"دانشجو {source.name}")

        try:
            result = enrollment.process_photos(source.name)
        except NotEnoughPhotosError as exc:
            report.append(
                f"{source.name}: only {exc.accepted} valid photo(s) "
                f"(minimum {config.MIN_PHOTOS}); rejected {exc.rejected}"
            )
            continue

        if result["rejected"]:
            report.append(f"{source.name}: rejected photos {result['rejected']}")

        folder = env["known_faces"] / source.name
        encodings = []
        for path in sorted(folder.iterdir())[: config.MAX_PHOTOS]:
            if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            try:
                encodings.append(
                    (path.name, recognition.encode_single_face(
                        enrollment._prepare_rgb(path)
                    ))
                )
            except Exception:
                continue
        photos[source.name] = encodings

    enrolled = {sid: items for sid, items in photos.items() if len(items) >= config.MIN_PHOTOS}
    assert len(enrolled) == len(REAL_STUDENT_DIRS), (
        f"only {len(enrolled)}/{len(REAL_STUDENT_DIRS)} students enrolled: {report}"
    )

    centroids = {
        sid: np.mean(np.stack([enc for _, enc in items]), axis=0)
        for sid, items in enrolled.items()
    }

    # Every student must recognise their own centroid.
    recognition._EMBEDDINGS = dict(centroids)
    self_failures = [
        f"{sid} matched {matched} (d={distance:.4f})"
        for sid in sorted(centroids)
        for matched, distance in [recognition.match_encoding(centroids[sid])]
        if matched != sid
    ]
    assert not self_failures, "self-match failed: " + "; ".join(self_failures)

    # Leave-one-out: the photo is unseen by the centroid that judges it.
    correct = 0
    wrong: list[str] = []
    rejected: list[str] = []
    for sid, items in sorted(enrolled.items()):
        for name, encoding in items:
            others = [enc for other_name, enc in items if other_name != name]
            leave_one_out = dict(centroids)
            leave_one_out[sid] = np.mean(np.stack(others), axis=0)
            recognition._EMBEDDINGS = leave_one_out

            matched, distance = recognition.match_encoding(encoding)
            if matched == sid:
                correct += 1
            elif matched is None:
                rejected.append(f"{sid}/{name} d={distance:.4f}")
            else:
                wrong.append(f"{sid}/{name} -> {matched} d={distance:.4f}")

    total = len(enrolled) and sum(len(items) for items in enrolled.values())
    recognition._EMBEDDINGS = None

    assert not wrong, (
        "WRONG identification (attendance would go to the wrong student): "
        + "; ".join(wrong)
        + f" | diagnostics: {'; '.join(report)}"
    )
    assert correct / total >= 0.7, (
        f"only {correct}/{total} photos recognised "
        f"(rejected: {'; '.join(rejected)})"
    )
