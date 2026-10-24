from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db, init_db
from ...models import Course
from ...schemas import CourseCreate, CourseResponse

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/", response_model=List[CourseResponse])
def get_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all courses."""
    init_db()
    courses = db.query(Course).offset(skip).limit(limit).all()
    return courses


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db)
):
    """Create a new course."""
    init_db()
    # Check if course_code already exists
    existing = db.query(Course).filter(Course.course_code == course_data.course_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course code {course_data.course_code} already exists"
        )
    db_course = Course(
        course_code=course_data.course_code,
        title=course_data.title,
        teacher=course_data.teacher,
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course