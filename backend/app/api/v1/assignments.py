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
from app.models import Role
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
    ResultBuckets,
)
from app.schemas.dashboard import AssignmentStats
from app.services import assignment_service, dashboard_service, submission_service

router = APIRouter(tags=["assignments"])


@router.get("/courses/{course_id}/assignments", response_model=list[AssignmentRead])
def list_assignments(
    course: MemberCourse,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    assignments = assignment_service.list_assignments(db, course, user, limit, offset)
    if user.role != Role.teacher:
        return assignments
    # The teacher's list also says how many students submitted and how they did.
    overview = dashboard_service.assignment_overview(db, course)
    enrolled = len(course.enrollments)
    items = []
    for assignment in assignments:
        read = AssignmentRead.model_validate(assignment)
        submitted, buckets = overview.get(assignment.id, (0, ResultBuckets()))
        read.submitted_count, read.result_buckets, read.enrolled_count = (
            submitted,
            buckets,
            enrolled,
        )
        items.append(read)
    return items


@router.post(
    "/courses/{course_id}/assignments",
    response_model=AssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(data: AssignmentCreate, course: OwnedCourse, db: DbSession):
    return assignment_service.create_assignment(db, course, data)


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment: MemberAssignment, db: DbSession, user: CurrentUser):
    read = AssignmentRead.model_validate(assignment)
    if user.role == Role.student:
        read.submissions_left = submission_service.submissions_left(db, user, assignment)
    return read


@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(data: AssignmentUpdate, assignment: OwnedAssignment, db: DbSession):
    return assignment_service.update_assignment(db, assignment, data)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment: OwnedAssignment, db: DbSession) -> None:
    assignment_service.delete_assignment(db, assignment)


@router.get("/assignments/{assignment_id}/stats", response_model=AssignmentStats)
def get_assignment_stats(assignment: OwnedAssignment, db: DbSession):
    """Pass rate per test and score distribution, from each student's best submission."""
    return dashboard_service.assignment_stats(db, assignment)
