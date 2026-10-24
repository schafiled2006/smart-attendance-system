from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Float, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ...config import DB_PATH

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), unique=True, nullable=False, comment="شماره دانشجویی")
    full_name = Column(String(100), nullable=False, comment="نام و نام خانوادگی")
    major = Column(String(50), nullable=True, comment=" رشته")
    term = Column(String(20), nullable=True, comment="ترم")
    embedding_file = Column(String(255), nullable=True, comment="مسیر فایل embedding")
    created_at = Column(DateTime, nullable=True, comment="تاریخ ایجاد")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(20), unique=True, nullable=False, comment="کد درس")
    title = Column(String(100), nullable=False, comment="عنوان درس")
    teacher = Column(String(100), nullable=True, comment="استاد")
    created_at = Column(DateTime, nullable=True, comment="تاریخ ایجاد")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(50), primary_key=True, comment="شناسه جلسه")
    course_id = Column(Integer, nullable=False, comment="id درس")
    start_time = Column(DateTime, nullable=False, comment="زمان شروع (ISO)")
    end_time = Column(DateTime, nullable=True, comment="زمان پایان")
    status = Column(String(20), nullable=False, comment="وضعیت: active / closed")
    late_threshold_minutes = Column(Integer, default=10, comment="آستانه تأخیر (دقیقه)")
    note = Column(Text, nullable=True, comment="لاحتیاطات")
    created_at = Column(DateTime, nullable=True, comment="تاریخ ایجاد")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False, comment="شنidere جلسه")
    student_id = Column(String(20), nullable=False, comment="شماره دانشجویی")
    full_name = Column(String(100), nullable=True, comment="نام کامل")
    status = Column(String(20), nullable=False, comment="وضعیت: present / late / absent")
    check_in_time = Column(DateTime, nullable=True, comment="ساعت ورود (فقط present/late)")
    confidence = Column(Float, nullable=True, comment="سطح مطابقة")
    camera_source = Column(String(30), nullable=True, comment="منبع دوربین: laptop / phone / manual")
    created_at = Column(DateTime, nullable=True, comment="تاریخ ثبت")

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uix_session_student"),
    )