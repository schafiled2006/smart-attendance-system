import os
import json
import numpy as np
import face_recognition
from ..config import DB_PATH, FACE_TOLERANCE

try:
    import sqlite3
    from .database import get_db
except ImportError:
    import sqlite3
    from database import get_db


def add_student(student_id: str, full_name: str, major: str = None,
                term: str = None, image_folder: str = None) -> dict:
    """
    Register a new student by processing images from a folder.

    - Minimum 3 and maximum 5 images from the folder are read
    - Average embedding is calculated and saved to embeddings/
    - Record is created in students table

    Returns dict with status and student info.
    """
    # Validate minimum images
    if image_folder:
        image_files = [f for f in os.listdir(image_folder)
                       if f.lower().endswith(('.jpg, .jpeg, .png, .jpg'))]

        if len(image_files) < 3:
            return {
                "success": False,
                "error": f"حداقل ۳ تصویر از {[image_folder]} نیاز دارید. "
                         f"تعداد یافت شده: {len(image_files)}"
            }

        if len(image_files) > 5:
            return {
                "success": False,
                "error": f"حداکثر ۵ تصویر مجاز است. "
                         f"تعداد یافت شده: {len(image_files)}"
            }

    # Calculate average embedding from images
    embeddings = []
    if image_folder:
        for image_file in sorted(image_files)[:5]:
            image_path = os.path.join(image_folder, image_file)
            try:
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)
                if face_encodings:
                    embeddings.append(face_encodings[0])
            except Exception as e:
                print(f"Warning: Could not process {image_path}: {e}")

    # Compute average embedding
    if not embeddings:
        return {
            "success": False,
            "error": "هیچ embedding معتبری از عکس‌ها استخراج نشد."
        }

    avg_embedding = np.mean(embeddings, axis=0)

    # Save embedding file
    embeddings_dir = Path(__file__).parent.parent / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    embedding_path = embeddings_dir / f"{student_id}.npy"
    np.save(str(embedding_path), avg_embedding)

    # Save to database
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO students (student_id, full_name, major, term, embedding_file, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (student_id, full_name, major, term,
             str(embedding_path),
             datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {
            "success": False,
            "error": f"شماره دانشجویی {student_id} قبلاً ثبت شده است."
        }
    finally:
        conn.close()

    return {
        "success": True,
        "student_id": student_id,
        "full_name": full_name,
        "embedding_file": str(embedding_path),
        "embedding_count": len(embeddings),
        "message": "دانشجو با موفقیت ثبت شد."
    }


def rebuild_embeddings() -> dict:
    """
    Rebuild all embeddings from known_faces folders.
    Useful after adding new images or restructuring.

    Returns dict with rebuild status.
    """
    known_faces_dir = Path(__file__).parent.parent / "known_faces"
    embeddings_dir = Path(__file__).parent.parent / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    # Get all student folders
    student_folders = [d for d in known_faces_dir.iterdir()
                       if d.is_dir()]

    rebuilt = 0
    failed = 0

    for student_folder in student_folders:
        student_id = student_folder.name
        image_files = [f for f in sorted(student_folder.iterdir())
                       if f.suffix.lower() in ('.jpg', '.jpeg', '.png')]

        if len(image_files) < 3:
            print(f"Warning: {student_id} has only {len(image_files)} images (min 3 required)")
            failed += 1
            continue

        embeddings = []
        for image_file in image_files[:5]:
            try:
                image = face_recognition.load_image_file(str(image_file))
                face_encodings = face_recognition.face_encodings(image)
                if face_encodings:
                    embeddings.append(face_encodings[0])
            except Exception as e:
                print(f"Warning: Could not process {image_file}: {e}")

        if not embeddings:
            print(f"Warning: No embeddings found for {student_id}")
            failed += 1
            continue

        avg_embedding = np.mean(embeddings, axis=0)
        embedding_path = embeddings_dir / f"{student_id}.npy"
        np.save(str(embedding_path), avg_embedding)
        rebuilt += 1

    return {
        "success": True,
        "rebuilt": rebuilt,
        "failed": failed,
        "total_students": len(student_folders),
        "message": f"{rebuilt} embedding rebuilt successfully. {failed} failed."
    }