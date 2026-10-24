from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db, init_db
from ...models import Student, Attendance
from ...schemas import AttendanceLog, AttendanceLogResponse
from ...services.attendance_service import log_attendance, mark_absent, process_recognition_result

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post("/recognize", response_model=dict)
def recognize_and_log(
    recognition_data: dict,
    db: Session = Depends(get_db)
):
    """Receive face recognition result and log attendance."""
    init_db()
    recognized_list = recognition_data.get("recognized_list", [])
    camera_source = recognition_data.get("camera_source", "laptop")

    if not recognized_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty recognized list"
        )

    results = process_recognition_result(recognized_list, camera_source)
    return {"results": results, "message": "Attendance processing complete"}


@router.post("/manual", response_model=dict)
def manual_attendance(
    student_id: str,
    status: str,  # "present", "late", "absent"
    db: Session = Depends(get_db)
):
    """Manually mark attendance for a student."""
    init_db()

    if status not in ["present", "late", "absent"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status}"
        )

    # Get active session
    from ...services.session_manager import get_active_session
    active = get_active_session()
    if not active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="هیچ جلسه فعال وجود ندارد"
        )

    session_id = active["session_id"]

    # Mark attendance manually
    if status == "absent":
        result = mark_absent(session_id, student_id)
    else:
        # For present/late, we need confidence - use default
        from ...services.attendance_service import log_attendance
        # Get confidence from recognition or default
        result = log_attendance(student_id, confidence=1.0, camera_source="manual")

    if not result.get("success"):
        if "قبلاً ثبت شده" in result.get("error", ""):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result.get("error")
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error")
        )

    return result