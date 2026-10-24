from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db, init_db
from ...models import Student, Course
from ...schemas import StudentCreate, StudentResponse

router = APIRouter(prefix="/api/students", tags=["students"])


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db)
):
    """Register a new student."""
    init_db()
    db_student = Student(
        student_id=student_data.student_id,
        full_name=student_data.full_name,
        major=student_data.major,
        term=student_data.term,
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.get("/", response_model=List[StudentResponse])
def get_students(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all students."""
    init_db()
    students = db.query(Student).offset(skip).limit(limit).all()
    return students


@router.delete("/{student_id}")
def delete_student(
    student_id: str,
    db: Session = Depends(get_db)
):
    """Delete a student by student_id."""
    init_db()
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    if db_student is None:
        raise HTTPException(
            status_code=status.HTTP_404_DETAIL,
            detail=f"Student with student_id {student_id} not found"
        )
    db.delete(db_student)
    db.commit()
    return {"message": f"Student {student_id} deleted successfully"}