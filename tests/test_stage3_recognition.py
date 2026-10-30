"""Stage 3 tests: recognition.py with synthetic vectors (and optional real photo).

Real-photo tests are skipped when ``tests/data/test_face.jpg`` is missing,
as agreed for this stage.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend import config, recognition
from backend.errors import InvalidInputError, NoFaceError

TEST_FACE = config.PROJECT_ROOT / "tests" / "data" / "test_face.jpg"


def _vector(deltas: dict[int, float] | None = None) -> np.ndarray:
    """Build a synthetic 128-d unit-ish vector from {index: value} deltas."""
    vector = np.zeros(128)
    for index, value in (deltas or {}).items():
        vector[index] = value
    return vector


# Two students that are clearly distinguishable from each other.
STUDENT_A = _vector({0: 0.4})
STUDENT_B = _vector({1: 0.4})


@pytest.fixture()
def temp_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate recognition from the real folders and reset the cache."""
    monkeypatch.setenv("ATTENDANCE_DB", str(tmp_path / "stage3_test.db"))
    embeddings_dir = tmp_path / "embeddings"
    known_faces_dir = tmp_path / "known_faces"
    embeddings_dir.mkdir()
    known_faces_dir.mkdir()
    monkeypatch.setattr(config, "EMBEDDINGS_DIR", embeddings_dir)
    monkeypatch.setattr(config, "KNOWN_FACES_DIR", known_faces_dir)
    recognition._EMBEDDINGS = None
    yield {"embeddings_dir": embeddings_dir}
    recognition._EMBEDDINGS = None


def _set_cache(student_vectors: dict[str, np.ndarray]) -> None:
    recognition._EMBEDDINGS = dict(student_vectors)


# --------------------------------------------------------------------------- #
# match_encoding with synthetic vectors
# --------------------------------------------------------------------------- #
def test_match_accepts_close_encoding(temp_env) -> None:
    _set_cache({"A": STUDENT_A})
    target = STUDENT_A + _vector({5: 0.05})  # small perturbation, dist 0.05

    student_id, distance = recognition.match_encoding(target)

    assert student_id == "A"
    assert distance == pytest.approx(float(np.linalg.norm(STUDENT_A - target)))
    assert distance <= config.FACE_TOLERANCE


def test_match_rejects_by_tolerance(temp_env) -> None:
    _set_cache({"A": STUDENT_A})
    target = _vector({60: 1.0})  # nothing like a known face

    student_id, distance = recognition.match_encoding(target)

    assert student_id is None
    assert distance == pytest.approx(float(np.linalg.norm(STUDENT_A - target)))
    assert distance > config.FACE_TOLERANCE


def test_match_rejects_by_margin(temp_env) -> None:
    _set_cache({"A": STUDENT_A, "B": STUDENT_B})
    # Roughly halfway between A and B so the two distances differ by < 0.05.
    target = _vector({0: 0.32, 1: 0.30})

    student_id, distance = recognition.match_encoding(target)

    distances = {sid: float(np.linalg.norm(vec - target)) for sid, vec in
                 (("A", STUDENT_A), ("B", STUDENT_B))}
    best = min(distances.values())
    second = max(distances.values())
    assert second < best + config.MATCH_MARGIN  # margin is genuinely violated
    assert distance == pytest.approx(best)
    assert student_id is None


def test_match_margin_skipped_with_single_student(temp_env) -> None:
    _set_cache({"A": STUDENT_A})
    # Close to A, but "not far enough" from a potential second match; with one
    # student the margin rule must not apply.
    target = _vector({0: 0.4, 1: 0.2})  # dist 0.2 to A only

    student_id, distance = recognition.match_encoding(target)

    assert student_id == "A"
    assert distance == pytest.approx(0.2)


def test_match_no_students_returns_none(temp_env) -> None:
    _set_cache({})

    student_id, distance = recognition.match_encoding(STUDENT_A)

    assert student_id is None
    assert distance == float("inf")


def test_match_prefers_nearest_of_two_students(temp_env) -> None:
    _set_cache({"A": STUDENT_A, "B": STUDENT_B})
    # Unambiguously close to A (dist 0.1) and far from B.
    target = _vector({0: 0.4, 1: 0.1})

    student_id, distance = recognition.match_encoding(target)

    assert student_id == "A"
    assert distance == pytest.approx(0.1)


# --------------------------------------------------------------------------- #
# reload_embeddings
# --------------------------------------------------------------------------- #
def test_reload_embeddings_counts_students_from_temp_dir(temp_env) -> None:
    embeddings_dir = temp_env["embeddings_dir"]
    np.save(embeddings_dir / "421234.npy", STUDENT_A)
    np.save(embeddings_dir / "423456.npy", STUDENT_B)
    np.save(embeddings_dir / "427890.npy", STUDENT_B + _vector({2: 0.3}))
    (embeddings_dir / "notes.txt").write_text("not an embedding", encoding="utf-8")

    count = recognition.reload_embeddings()

    assert count == 3
    student_id, distance = recognition.match_encoding(STUDENT_A)
    assert student_id == "421234"
    assert distance == pytest.approx(0.0)


def test_reload_embeddings_skips_invalid_files(temp_env) -> None:
    embeddings_dir = temp_env["embeddings_dir"]
    np.save(embeddings_dir / "421234.npy", STUDENT_A)
    np.save(embeddings_dir / "bad_shape.npy", np.zeros((64,)))
    np.save(embeddings_dir / "empty.npy", np.zeros(0))
    (embeddings_dir / "corrupt.npy").write_bytes(b"not a real npy file")

    count = recognition.reload_embeddings()

    assert count == 1
    assert set(recognition._EMBEDDINGS) == {"421234"}


def test_reload_embeddings_skips_nonfinite_vectors(temp_env) -> None:
    # Guard for the NaN/Inf bug: finite-check must reject such vectors,
    # otherwise both rejection comparisons (also NaN) would accept a match.
    embeddings_dir = temp_env["embeddings_dir"]
    np.save(embeddings_dir / "all_nan.npy", np.full(128, np.nan))
    np.save(embeddings_dir / "all_inf.npy", np.full(128, np.inf))
    np.save(embeddings_dir / "421234.npy", STUDENT_A)

    count = recognition.reload_embeddings()

    assert count == 1
    assert set(recognition._EMBEDDINGS) == {"421234"}
    student_id, distance = recognition.match_encoding(STUDENT_A)
    assert student_id == "421234"
    assert distance == pytest.approx(0.0)


def test_reload_embeddings_empty_dir_and_lazy_load(temp_env) -> None:
    # Nothing in the temp embeddings dir; lazy load inside match_encoding.
    student_id, distance = recognition.match_encoding(STUDENT_A)
    assert recognition._EMBEDDINGS == {}
    assert student_id is None
    assert distance == float("inf")

    np.save(temp_env["embeddings_dir"] / "421234.npy", STUDENT_A)
    assert recognition.reload_embeddings() == 1
    student_id, _ = recognition.match_encoding(STUDENT_A)
    assert student_id == "421234"


# --------------------------------------------------------------------------- #
# recognize_frame (logic tested with fake detection, no real photos needed)
# --------------------------------------------------------------------------- #
def test_recognize_frame_downscales_and_returns_relative_boxes(
    temp_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_cache({"A": STUDENT_A, "B": STUDENT_B})
    seen_shapes: list[tuple[int, int]] = []

    def fake_face_locations(rgb, model=None):
        seen_shapes.append((rgb.shape[0], rgb.shape[1]))
        assert model == config.DETECTION_MODEL
        # Coordinates as returned by dlib: (top, right, bottom, left).
        return [(20, 200, 120, 100)]

    def fake_face_encodings(rgb, known_face_locations=None):
        return [STUDENT_A + _vector({9: 0.05})]  # unambiguous match with A

    monkeypatch.setattr(recognition.face_recognition, "face_locations", fake_face_locations)
    monkeypatch.setattr(
        recognition.face_recognition, "face_encodings", fake_face_encodings
    )

    frame = np.zeros((480, 1280, 3), dtype=np.uint8)
    results = recognition.recognize_frame(frame)

    assert len(results) == 1
    result = results[0]
    assert result["student_id"] == "A"
    assert result["distance"] == pytest.approx(0.05)
    top, right, bottom, left = result["box"]
    # Relative to the ORIGINAL frame size, regardless of downscaling.
    assert top == pytest.approx(20 / 480)
    assert right == pytest.approx(200 / 1280)
    assert bottom == pytest.approx(120 / 480)
    assert left == pytest.approx(100 / 1280)
    assert all(0.0 <= value <= 1.0 for value in result["box"])
    # Detection had to run on a downscaled frame (width <= FRAME_MAX_WIDTH).
    assert seen_shapes == [(240, 640)]


def test_recognize_frame_small_frame_not_resized(
    temp_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_cache({"A": STUDENT_A})
    seen_shapes: list[tuple[int, int]] = []

    def fake_face_locations(rgb, model=None):
        seen_shapes.append((rgb.shape[0], rgb.shape[1]))
        return []

    monkeypatch.setattr(recognition.face_recognition, "face_locations", fake_face_locations)

    frame = np.zeros((160, 320, 3), dtype=np.uint8)
    assert recognition.recognize_frame(frame) == []
    assert seen_shapes == [(160, 320)]  # no resize happened


def test_recognize_frame_returns_unknown_without_student_id(
    temp_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_cache({"A": STUDENT_A})

    monkeypatch.setattr(
        recognition.face_recognition,
        "face_locations",
        lambda rgb, model=None: [(0, 40, 40, 0)],
    )
    monkeypatch.setattr(
        recognition.face_recognition,
        "face_encodings",
        lambda rgb, known_face_locations=None: [_vector({90: 1.0})],
    )

    results = recognition.recognize_frame(np.zeros((80, 80, 3), dtype=np.uint8))

    assert len(results) == 1
    assert results[0]["student_id"] is None
    assert results[0]["distance"] > config.FACE_TOLERANCE
    assert results[0]["box"] == (0.0, 0.5, 0.5, 0.0)


def test_recognize_frame_grayscale_input(
    temp_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Guard for the channel-normalization fix: 2-D (grayscale) frames must
    # work instead of crashing in cv2.cvtColor.
    _set_cache({"A": STUDENT_A})
    monkeypatch.setattr(
        recognition.face_recognition,
        "face_locations",
        lambda rgb, model=None: [(10, 50, 60, 20)],
    )
    monkeypatch.setattr(
        recognition.face_recognition,
        "face_encodings",
        lambda rgb, known_face_locations=None: [STUDENT_A],
    )

    results = recognition.recognize_frame(np.zeros((70, 60), dtype=np.uint8))

    assert len(results) == 1
    assert results[0]["student_id"] == "A"
    assert results[0]["box"] == pytest.approx(
        (10 / 70, 50 / 60, 60 / 70, 20 / 60)
    )


def test_recognize_frame_bgra_input(
    temp_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_cache({"A": STUDENT_A})
    monkeypatch.setattr(
        recognition.face_recognition,
        "face_locations",
        lambda rgb, model=None: [],
    )

    rgba_frame = np.zeros((80, 80, 4), dtype=np.uint8)
    assert recognition.recognize_frame(rgba_frame) == []


def test_recognize_frame_invalid_channel_count_raises(temp_env) -> None:
    with pytest.raises(InvalidInputError):
        recognition.recognize_frame(np.zeros((16, 16, 2), dtype=np.uint8))


# --------------------------------------------------------------------------- #
# load_image_rgb / encode_single_face
# --------------------------------------------------------------------------- #
def test_load_image_rgb_returns_three_channel_array(
    temp_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image

    image_path = temp_env["embeddings_dir"].parent / "tiny.png"
    Image.new("RGB", (4, 2), color=(0, 128, 255)).save(image_path)

    rgb = recognition.load_image_rgb(image_path)

    assert rgb.shape == (2, 4, 3)
    assert rgb.dtype == np.uint8
    assert rgb[0, 0].tolist() == [0, 128, 255]  # RGB order, not BGR


@pytest.mark.skipif(not TEST_FACE.exists(), reason="tests/data/test_face.jpg missing")
def test_encode_single_face_on_real_photo(temp_env) -> None:
    rgb = recognition.load_image_rgb(TEST_FACE)
    encoding = recognition.encode_single_face(rgb)
    assert encoding.shape == (128,)


def test_encode_single_face_blank_image_raises_no_face(temp_env) -> None:
    blank = np.zeros((120, 120, 3), dtype=np.uint8)
    with pytest.raises(NoFaceError):
        recognition.encode_single_face(blank)


def test_encode_single_face_two_faces_raises(
    temp_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.errors import MultipleFacesError

    monkeypatch.setattr(
        recognition.face_recognition,
        "face_locations",
        lambda rgb, model=None: [(0, 20, 20, 0), (20, 40, 40, 20)],
    )
    monkeypatch.setattr(
        recognition.face_recognition,
        "face_encodings",
        lambda rgb, known_face_locations=None: [STUDENT_A, STUDENT_B],
    )
    with pytest.raises(MultipleFacesError):
        recognition.encode_single_face(np.zeros((40, 40, 3), dtype=np.uint8))
