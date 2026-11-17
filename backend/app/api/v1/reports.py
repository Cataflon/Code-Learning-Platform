from fastapi import APIRouter

from app.core.deps import DbSession, MemberCourse, OwnedCourse, StudentUser
from app.schemas.report import ClassConceptReport, StudentConceptReport
from app.services import report_service

router = APIRouter(prefix="/courses/{course_id}/reports", tags=["reports"])


@router.get("/concepts/me", response_model=StudentConceptReport)
def my_concept_report(course: MemberCourse, user: StudentUser, db: DbSession):
    """The student's own report: what they master and what they should review."""
    return report_service.student_concept_report(db, user, course)


@router.get("/concepts", response_model=ClassConceptReport)
def class_concept_report(course: OwnedCourse, db: DbSession):
    """The whole class, per concept, for the course teacher."""
    return report_service.class_concept_report(db, course)
