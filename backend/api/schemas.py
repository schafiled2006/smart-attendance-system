"""Pydantic request and response schemas for the API."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str = "ok"


class StudentCreate(BaseModel):
    student_id: str
    full_name: str
    major: str = ""
    term: str = ""


class StudentUpdate(BaseModel):
    full_name: str | None = None
    major: str | None = None
    term: str | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: str
    full_name: str
    major: str = ""
    term: str = ""
    embedding_path: str | None = None
    photo_count: int = 0
    created_at: str
    has_embedding: bool = False


class ProcessPhotosResponse(BaseModel):
    accepted: int
    rejected: list[dict]
    warnings: list[dict]
    embedding_saved: bool


class CourseResponse(BaseModel):
    id: int
    title: str
    teacher: str = ""
    room: str = ""


class SessionStartRequest(BaseModel):
    course_id: int = 1
    late_after_minutes: int | None = None


class SessionCloseRequest(BaseModel):
    session_id: int | None = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    started_at: str
    ended_at: str | None = None
    late_after_minutes: int
    status: str


class AttendanceItem(BaseModel):
    student_id: str
    full_name: str
    major: str = ""
    term: str = ""
    status: str
    checked_at: str | None = None
    source: str | None = None


class SessionSummary(BaseModel):
    total: int
    present: int
    late: int
    absent: int


class SessionAttendanceResponse(BaseModel):
    attendance: list[AttendanceItem]
    summary: SessionSummary


class FaceItem(BaseModel):
    box: tuple[float, float, float, float]
    student_id: str | None = None
    distance: float


class RecognitionResponse(BaseModel):
    recorded: list[str]
    already_present: list[str]
    pending: dict[str, int]
    unknown_count: int
    faces: list[FaceItem]


class ErrorResponse(BaseModel):
    error: str
    message: str
