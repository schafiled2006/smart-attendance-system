"""Central configuration for the attendance system.

Every configurable value and every path lives here; other modules must import
from this module instead of hard-coding values.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Face recognition
FACE_TOLERANCE = 0.55            # must stay between 0.5 and 0.6
MATCH_MARGIN = 0.05              # required gap between best and second best match
MIN_PHOTOS = 3
MAX_PHOTOS = 5
REQUIRED_CONSECUTIVE_FRAMES = 3
DEFAULT_LATE_AFTER_MINUTES = 10
DETECTION_MODEL = "hog"
FRAME_MAX_WIDTH = 640            # frames are downscaled before detection
PHOTO_MAX_SIDE = 1280
TIMEZONE = "Asia/Tehran"
CAMERA_SOURCE: int | str = 0     # or "http://<ip>:8080/video" for IP Webcam
PROCESS_EVERY_N_FRAMES = 3       # only used by main_test.py

# API
API_HOST = "127.0.0.1"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173"]

# Directories (all relative to the project root)
KNOWN_FACES_DIR = PROJECT_ROOT / "known_faces"
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "app.log"
DATA_DIR = PROJECT_ROOT / "data"


def get_db_path() -> Path:
    """Return the SQLite path, honouring the ATTENDANCE_DB override."""
    override = os.environ.get("ATTENDANCE_DB")
    if override:
        return Path(override).expanduser().resolve()
    return DATA_DIR / "attendance.db"


DB_PATH = get_db_path()
