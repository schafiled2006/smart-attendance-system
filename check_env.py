"""Verify that the Python environment is ready for the attendance system.

Run with the project virtualenv:

    venv\\Scripts\\python.exe check_env.py

The script checks every required import, the configured directories, the
Asia/Tehran timezone and finally runs ``face_recognition.face_encodings`` on
the first image found in ``tests/data/`` (if any).
"""
from __future__ import annotations

import sys
import traceback
from importlib import metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend import config  # noqa: E402

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

DISTRIBUTION_NAMES = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "dlib": "dlib-bin",
    "python_multipart": "python-multipart",
}


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def _module_version(module_name: str, module) -> str:
    distribution = DISTRIBUTION_NAMES.get(module_name, module_name)
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return str(getattr(module, "__version__", "unknown"))


def check_imports() -> list[str]:
    """Import every required module and report its version."""
    _print_header("Imports")
    failures: list[str] = []
    for name in REQUIRED_MODULES:
        try:
            module = __import__(name)
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(name)
            print(f"[FAIL] {name}: {exc}")
            traceback.print_exc(limit=1)
            continue
        print(f"[OK]   {name} {_module_version(name, module)}")
    return failures


def check_python() -> list[str]:
    _print_header("Python")
    print(f"executable: {sys.executable}")
    print(f"version:    {sys.version.split()[0]}")
    if sys.version_info[:2] != (3, 11):
        print("[WARN] Python 3.11 is required by PROJECT_CONTEXT.md.")
        return ["python_version"]
    print("[OK]   Python 3.11")
    return []


def check_numpy() -> list[str]:
    _print_header("NumPy")
    import numpy

    major = int(numpy.__version__.split(".")[0])
    if major >= 2:
        print(f"[FAIL] numpy {numpy.__version__} is >= 2; the project pins numpy<2.")
        return ["numpy_version"]
    print(f"[OK]   numpy {numpy.__version__} (< 2)")
    return []


def check_timezone() -> list[str]:
    _print_header("Timezone")
    try:
        from zoneinfo import ZoneInfo

        zone = ZoneInfo(config.TIMEZONE)
        print(f"[OK]   {config.TIMEZONE} -> {zone}")
        return []
    except Exception as exc:  # pragma: no cover - failure path
        print(f"[FAIL] timezone {config.TIMEZONE}: {exc}")
        return ["timezone"]


def check_directories() -> list[str]:
    _print_header("Directories")
    failures: list[str] = []
    for directory in (
        config.KNOWN_FACES_DIR,
        config.EMBEDDINGS_DIR,
        config.REPORTS_DIR,
        config.LOGS_DIR,
        config.DATA_DIR,
        PROJECT_ROOT / "tests" / "data",
    ):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"[OK]   {directory}")
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(str(directory))
            print(f"[FAIL] {directory}: {exc}")
    return failures


def check_face_encodings() -> list[str]:
    _print_header("Face recognition")
    import face_recognition
    import numpy as np
    from PIL import Image, ImageOps

    images = sorted(
        path
        for path in (PROJECT_ROOT / "tests" / "data").glob("*")
        if path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not images:
        print(
            "[SKIP] No test image found in tests/data/. "
            "Place a JPG/PNG photo with a face there to run this check."
        )
        return []

    path = images[0]
    print(f"image: {path}")
    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((config.PHOTO_MAX_SIDE, config.PHOTO_MAX_SIDE))
            rgb = np.array(image)

        locations = face_recognition.face_locations(rgb, model=config.DETECTION_MODEL)
        encodings = face_recognition.face_encodings(
            rgb, known_face_locations=locations
        )
    except Exception as exc:  # pragma: no cover - failure path
        print(f"[FAIL] face_encodings raised: {exc}")
        traceback.print_exc(limit=2)
        return ["face_encodings"]

    print(f"faces detected: {len(locations)}")
    if not encodings:
        print("[FAIL] face_recognition.face_encodings returned no encoding.")
        return ["face_encodings"]

    print(f"encodings: {len(encodings)}, shape: {encodings[0].shape}")
    if encodings[0].shape != (128,):
        print("[FAIL] expected a 128-dimensional encoding.")
        return ["face_encodings"]
    print("[OK]   face_recognition.face_encodings")
    return []


def main() -> int:
    failures: list[str] = []
    failures += check_python()
    failures += check_imports()
    failures += check_numpy()
    failures += check_timezone()
    failures += check_directories()
    failures += check_face_encodings()

    _print_header("Result")
    if failures:
        print(f"[FAIL] {len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("[OK] Environment is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
