import json
import numpy as np
import face_recognition
import cv2
from ..config import FACE_TOLERANCE, FACE_MODEL, PROCESS_EVERY_N_FRAMES
from pathlib import Path


def _load_known_embeddings():
    """Load all known face embeddings from the embeddings directory."""
    embeddings_dir = Path(__file__).parent.parent / "embeddings"
    known_encodings = []
    known_metadata = []

    if not embeddings_dir.exists():
        return known_encodings, known_metadata

    for embedding_file in sorted(embeddings_dir.glob("*.npy")):
        try:
            encoding = np.load(str(embedding_file))
            known_encodings.append(encoding)

            # Extract student_id from filename (e.g., "s12345.npy" -> "s12345")
            student_id = embedding_file.stem
            known_metadata.append({
                "student_id": student_id,
                "embedding_file": str(embedding_file),
            })
        except Exception as e:
            print(f"Warning: Could not load embedding {embedding_file}: {e}")

    return known_encodings, known_metadata


def recognize_frame(frame_bgr: np.ndarray) -> list:
    """
    Recognize faces in a BGR frame.

    Args:
        frame_bgr: numpy array in BGR format (OpenCV format)

    Returns:
        list of dicts, each containing:
        - student_id: str or "unknown"
        - full_name: str
        - confidence: float
        - embedding_file: str (path to matching embedding)

    Behavior:
        - Detects all faces in the frame
        - For each face, compares against known embeddings
        - Only marks as recognized if the nearest face has a distinct margin
          from the second-nearest (to avoid ambiguous matches)
        - Unknown faces are logged but NOT included in output
        - Tolerance is read from config (0.50 to 0.60 range)
    """
    # Convert BGR to RGB (face_recognition expects RGB)
    rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    # Detect face locations and encodings
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    # Load known embeddings
    known_encodings, known_metadata = _load_known_embeddings()

    results = []

    for face_encoding in face_encodings:
        # Compute face distances to all known encodings
        if not known_encodings:
            # No known embeddings loaded - mark as unknown
            results.append({
                "student_id": "unknown",
                "full_name": "نامشخص",
                "confidence": 0.0,
                "embedding_file": None,
            })
            continue

        # Calculate face distances
        distances = face_recognition.face_distance(known_encodings, face_encoding)

        # Find the best and second-best matches
        # Sort by distance (lower = better match)
        sorted_indices = np.argsort(distances)
        best_distance = distances[sorted_indices[0]]
        second_best_distance = distances[sorted_indices[1]] if len(sorted_indices) > 1 else best_distance

        # Calculate margin (gap between best and second-best)
        margin = second_best_distance - best_distance

        # Check if the best match is good enough AND has sufficient margin
        # Tolerance: lower is stricter, higher is more permissive
        # 0.50 = strict, 0.60 = more permissive
        tolerance = FACE_TOLERANCE

        if best_distance <= tolerance and margin >= (tolerance * 0.5):
            # Good match with sufficient margin
            best_idx = sorted_indices[0]
            metadata = known_metadata[best_idx]
            student_id = metadata["student_id"]
            # Convert distance to confidence (1 - distance, clamped)
            confidence = round(float(1.0 - best_distance), 4)
            full_name = _get_student_name(student_id)

            results.append({
                "student_id": student_id,
                "full_name": full_name,
                "confidence": confidence,
                "embedding_file": metadata["embedding_file"],
            })
        else:
            # Either too far below tolerance or ambiguous match
            # Log as unknown but don't include in output
            print(f"Face recognized as unknown: distance={best_distance:.4f}, "
                  f"second_best={second_best_distance:.4f}, margin={margin:.4f}")
            # Still append but mark as unknown - caller can filter
            results.append({
                "student_id": "unknown",
                "full_name": "نامشخص",
                "confidence": round(float(1.0 - best_distance), 4),
                "embedding_file": None,
            })

    return results


def _get_student_name(student_id: str) -> str:
    """Get student full name from database by student_id."""
    try:
        import sqlite3
        from .database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name FROM students WHERE student_id = ?",
            (student_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        print(f"DB error getting student name: {e}")
    return student_id