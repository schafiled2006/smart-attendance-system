from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db, init_db
from ...services.report_service import export_session_excel

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/session/{session_id}/excel")
def get_session_excel(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Export session attendance to Excel."""
    init_db()
    result = export_session_excel(session_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    return result


@router.get("/daily", response_model=dict)
def get_daily_report(
    db: Session = Depends(get_db)
):
    """Get daily attendance report."""
    init_db()
    from ...services.session_manager import get_active_session
    active = get_active_session()
    if not active:
        return {"message": "هیچ جلسه فعالی وجود ندارد", "records": []}

    # Get attendance for the active session
    conn = ...  # would need actual DB connection
    # For now, return basic info
    return {
        "message": "روزانه گزارش",
        "session_id": active.get("session_id"),
    }