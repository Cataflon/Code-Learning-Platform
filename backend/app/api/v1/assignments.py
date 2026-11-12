from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import (
    CurrentUser,
    DbSession,
    MemberAssignment,
    MemberCourse,
    OwnedAssignment,
    OwnedCourse,
)
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from app.services import assignment_service

router = APIRouter(tags=["assignments"])


@router.get("/courses/{course_id}/assignments", response_model=list[AssignmentRead])
def list_assignments(
    course: MemberCourse,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return assignment_service.list_assignments(db, course, user, limit, offset)


@router.post(
    "/courses/{course_id}/assignments",
    response_model=AssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(data: AssignmentCreate, course: OwnedCourse, db: DbSession):
    return assignment_service.create_assignment(db, course, data)


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment: MemberAssignment):
    return assignment


@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(data: AssignmentUpdate, assignment: OwnedAssignment, db: DbSession):
    return assignment_service.update_assignment(db, assignment, data)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment: OwnedAssignment, db: DbSession) -> None:
    assignment_service.delete_assignment(db, assignment)
