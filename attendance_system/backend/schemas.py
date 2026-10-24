from pydantic import BaseModel, Field, conint
from typing import Optional
from datetime import datetime


# Student schemas
class StudentCreate(BaseModel):
    student_id: str = Field(..., description="شماره دانشجویی (UNIQUE)")
    full_name: str = Field(..., description="نام و نام خانوادگی")
    major: Optional[str] = Field(None, description=" رشته")
    term: Optional[str] = Field(None, description="ترم")


class StudentResponse(StudentCreate):
    id: int
    embedding_file: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Course schemas
class CourseCreate(BaseModel):
    course_code: str = Field(..., description="کد درس (UNIQUE)")
    title: str = Field(..., description="عنوان درس")
    teacher: Optional[str] = Field(None, description="اسم استاد")


class CourseResponse(CourseCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Session schemas
class SessionStart(BaseModel):
    course_id: int = Field(..., description="id درس")
    late_threshold_minutes: int = Field(
        10, description="آستانه تأخیر در دقیقه (پیش‌فرض 10)"
    )
    note: str = Field("", description="یادداشت اختیاری")


class SessionResponse(BaseModel):
    session_id: str
    course_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    late_threshold_minutes: int
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


# Attendance schemas
class AttendanceLog(BaseModel):
    student_id: str = Field(..., description="شماره دانشجویی")
    confidence: float = Field(..., description="سطح مطابقة چهره")
    camera_source: str = Field(
        "laptop", description="منبع دوربین: laptop / phone / manual"
    )


class AttendanceLogResponse(BaseModel):
    student_id: str
    full_name: str
    status: str  # present / late / absent
    check_in_time: Optional[str] = None
    confidence: float
    camera_source: str


# Recognition result schema
class RecognitionResult(BaseModel):
    recognized_list: list[dict] = Field(
        ..., description="لیست Dictionary each: {student_id, full_name, confidence}"
    )


# Report schemas
class StudentAttendanceRecord(BaseModel):
    student_id: str
    full_name: str
    major: Optional[str] = None
    term: Optional[str] = None
    status: str
    check_in_time: Optional[str] = None
    confidence: Optional[float] = None


class SessionReportResponse(BaseModel):
    session_id: str
    course_title: str
    date: str
    records: list[StudentAttendanceRecord]
    total_students: int
    present_count: int
    late_count: int
    absent_count: int