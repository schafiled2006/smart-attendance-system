from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db, init_db
from ...models import Session as SessionModel
from ...schemas import SessionStart, SessionResponse

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_new_session(
    session_data: SessionStart,
    db: Session = Depends(get_db)
):
    """Start a new attendance session."""
    init_db()
    result = start_session(
        course_id=session_data.course_id,
        late_threshold_minutes=session_data.late_threshold_minutes,
        note=session_data.note
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Could not start session")
        )
    return result


@router.post("/{session_id}/close", status_code=status.HTTP_200_OK)
def close_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Close a specific session."""
    init_db()
    result = close_session(session_id=session_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Session not found")
        )
    return {"message": result.get("message")}


@router.get("/active", response_model=dict)
def get_active_session_endpoint(
    db: Session = Depends(get_db)
):
    """Get the currently active session."""
    init_db()
    result = get_active_session()
    if result is None:
        return {"session_id": None, "message": "هیچ جلسه فعالی فعال نیست"}
    return result


@router.get("/", response_model=List[dict])
def get_all_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all sessions."""
    init_db()
    from ...models import Session
    sessions = db.query(Session).offset(skip).limit(limit).all()
    return [dict(s) for s in sessions]