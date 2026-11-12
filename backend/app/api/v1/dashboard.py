from fastapi import APIRouter

from app.core.deps import DbSession, StudentUser
from app.schemas.dashboard import StudentDashboard
from app.services import dashboard_service

router = APIRouter(prefix="/me", tags=["dashboard"])


@router.get("/dashboard", response_model=StudentDashboard)
def get_dashboard(user: StudentUser, db: DbSession):
    """Everything the student's start page shows, in one request."""
    return dashboard_service.student_dashboard(db, user)
