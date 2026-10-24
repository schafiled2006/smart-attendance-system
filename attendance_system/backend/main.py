from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.students import router as students_router
from .routers.courses import router as courses_router
from .routers.sessions import router as sessions_router
from .routers.attendance import router as attendance_router
from .routers.reports import router as reports_router

# Initialize database on startup
from .database import init_db
init_db()

app = FastAPI(
    title="Smart Attendance System - Backend",
    description="Backend-only API for Smart Attendance System with face recognition",
    version="1.0.0",
)

# CORS configuration for React frontend (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(students_router)
app.include_router(courses_router)
app.include_router(sessions_router)
app.include_router(attendance_router)
app.include_router(reports_router)


@app.get("/api/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    from .database import check_db_health
    db_status = check_db_health()
    return {
        "status": "healthy",
        "service": "smart-attendance-backend",
        "database": db_status,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


@app.get("/", include_in_schema=False)
def root():
    """Root endpoint returning API info."""
    return {
        "message": "Smart Attendance System Backend API",
        "docs": "/docs",
        "version": "1.0.0"
    }