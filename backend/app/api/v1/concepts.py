from fastapi import APIRouter, status

from app.core.deps import DbSession, MemberCourse, OwnedCourse
from app.schemas.course import ConceptCreate, ConceptRead
from app.services import course_service

router = APIRouter(prefix="/courses/{course_id}/concepts", tags=["concepts"])


@router.get("", response_model=list[ConceptRead])
def list_concepts(course: MemberCourse, db: DbSession):
    return course_service.list_concepts(db, course)


@router.post("", response_model=ConceptRead, status_code=status.HTTP_201_CREATED)
def create_concept(data: ConceptCreate, course: OwnedCourse, db: DbSession):
    return course_service.create_concept(db, course, data)
