"""FastAPI application shell (routes only, no business logic).

Implemented in stage 8.
"""
from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import Body, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend import (
    attendance_service,
    config,
    database,
    enrollment,
    recognition,
    report_service,
    session_manager,
)
from backend.api.schemas import (
    CourseResponse,
    HealthResponse,
    ProcessPhotosResponse,
    RecognitionResponse,
    SessionAttendanceResponse,
    SessionCloseRequest,
    SessionResponse,
    SessionStartRequest,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)
from backend.errors import (
    AppError,
    InvalidInputError,
    MultipleFacesError,
    NoActiveSessionError,
    NoFaceError,
    NotEnoughPhotosError,
    PayloadTooLargeError,
    ReportEmptyError,
    SessionAlreadyActiveError,
    SessionClosedError,
    SessionNotFoundError,
    StudentExistsError,
    StudentHasAttendanceError,
    StudentNotFoundError,
)
from backend.utils import normalize_digits, setup_logging

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

ERROR_STATUS_MAP: dict[type[AppError], int] = {
    StudentNotFoundError: 404,
    SessionNotFoundError: 404,
    ReportEmptyError: 404,
    StudentExistsError: 409,
    SessionAlreadyActiveError: 409,
    StudentHasAttendanceError: 409,
    SessionClosedError: 409,
    NoActiveSessionError: 409,
    InvalidInputError: 422,
    NotEnoughPhotosError: 422,
    NoFaceError: 422,
    MultipleFacesError: 422,
    PayloadTooLargeError: 413,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    database.init_db()
    yield


app = FastAPI(
    title="Smart Attendance API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    status_code = 400
    for err_cls, code in ERROR_STATUS_MAP.items():
        if isinstance(exc, err_cls):
            status_code = code
            break
    return JSONResponse(
        status_code=status_code,
        content={"error": exc.code, "message": exc.message_fa},
    )


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "invalid_input", "message": "ورودی نامعتبر است."},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": str(exc.detail)},
    )


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
# Students
# --------------------------------------------------------------------------- #
@app.get("/students", response_model=list[StudentResponse])
def get_students():
    return enrollment.list_students()


@app.post("/students", response_model=StudentResponse)
def create_student(payload: StudentCreate):
    return enrollment.add_student(
        student_id=payload.student_id,
        full_name=payload.full_name,
        major=payload.major,
        term=payload.term,
    )


@app.put("/students/{id}", response_model=StudentResponse)
def update_student(id: str, payload: StudentUpdate):
    cleaned_id = normalize_digits(id)
    return enrollment.update_student(
        student_id=cleaned_id,
        full_name=payload.full_name,
        major=payload.major,
        term=payload.term,
    )


@app.delete("/students/{id}")
def delete_student(id: str, force: bool = False):
    cleaned_id = normalize_digits(id)
    success = enrollment.delete_student(student_id=cleaned_id, force=force)
    return {"success": success, "student_id": cleaned_id}


@app.post("/students/{id}/process-photos", response_model=ProcessPhotosResponse)
def process_photos(id: str):
    cleaned_id = normalize_digits(id)
    return enrollment.process_photos(student_id=cleaned_id)


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
@app.get("/courses", response_model=list[CourseResponse])
def get_courses():
    return session_manager.list_courses()


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
@app.post("/sessions/start", response_model=SessionResponse)
def start_session(payload: SessionStartRequest | None = None):
    body = payload or SessionStartRequest()
    return session_manager.start_session(
        course_id=body.course_id,
        late_after_minutes=body.late_after_minutes,
    )


@app.post("/sessions/close", response_model=SessionResponse)
def close_session(payload: SessionCloseRequest | None = None):
    target_id = payload.session_id if payload is not None else None
    return session_manager.close_session(session_id=target_id)


@app.get("/sessions/active", response_model=SessionResponse | None)
def get_active_session():
    return session_manager.get_active_session()


@app.get("/sessions", response_model=list[SessionResponse])
def get_sessions(limit: int = 50):
    return session_manager.list_sessions(limit=limit)


# --------------------------------------------------------------------------- #
# Attendance & Recognition
# --------------------------------------------------------------------------- #
@app.get("/sessions/{id}/attendance", response_model=SessionAttendanceResponse)
def get_session_attendance(id: int):
    attendance = attendance_service.get_session_attendance(id)
    summary = attendance_service.get_session_summary(id)
    return {
        "attendance": attendance,
        "summary": summary,
    }


@app.post("/sessions/{id}/recognize", response_model=RecognitionResponse)
def recognize(id: int, file: UploadFile = File(...)):
    # Verify session exists and is active before doing heavy image processing
    session = session_manager.get_session(id)
    if session["status"] != "active":
        raise NoActiveSessionError()

    contents = file.file.read()
    if not contents:
        raise InvalidInputError("فایل تصویر خالی است.")
    if len(contents) > MAX_IMAGE_SIZE:
        raise PayloadTooLargeError()

    nparr = np.frombuffer(contents, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise InvalidInputError("فایل ارسالی تصویر معتبری نیست.")

    matches = recognition.recognize_frame(bgr)
    result = attendance_service.process_recognition_result(
        session_id=id, matches=matches
    )
    result["faces"] = [
        {
            "box": match["box"],
            "student_id": match["student_id"],
            "distance": match["distance"],
        }
        for match in matches
    ]
    return result


@app.put("/sessions/{id}/attendance/{student_id}")
def log_manual_attendance(id: int, student_id: str):
    cleaned_id = normalize_digits(student_id)
    success = attendance_service.log_attendance(
        session_id=id,
        student_id=cleaned_id,
        source="manual",
    )
    result = {"success": success, "session_id": id, "student_id": cleaned_id}
    if not success:
        result["reason"] = "already_present"
    return result


@app.delete("/sessions/{id}/attendance/{student_id}")
def remove_manual_attendance(id: int, student_id: str):
    cleaned_id = normalize_digits(student_id)
    success = attendance_service.remove_attendance(
        session_id=id,
        student_id=cleaned_id,
    )
    return {"success": success, "session_id": id, "student_id": cleaned_id}


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
@app.get("/sessions/{id}/report")
def export_session_report(id: int):
    file_path = report_service.export_session_report(session_id=id)
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/reports/daily")
def export_daily_report(date: str = Query(...)):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise InvalidInputError("فرمت تاریخ باید YYYY-MM-DD باشد.")
    file_path = report_service.export_daily_report(date_iso=date)
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
