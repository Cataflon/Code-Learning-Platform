"""Business rules and queries for assignments."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models import Assignment, Course, Role, User
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate


def create_assignment(db: Session, course: Course, data: AssignmentCreate) -> Assignment:
    assignment = Assignment(course_id=course.id, **data.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def list_assignments(
    db: Session, course: Course, viewer: User, limit: int = 100, offset: int = 0
) -> list[Assignment]:
    """Students only see published assignments."""
    query = (
        select(Assignment)
        .where(Assignment.course_id == course.id)
        .options(selectinload(Assignment.test_cases))
    )
    if viewer.role == Role.student:
        query = query.where(Assignment.is_published.is_(True))
    query = query.order_by(Assignment.due_at.nulls_last(), Assignment.id).limit(limit)
    return list(db.scalars(query.offset(offset)))


def get_assignment(db: Session, assignment_id: int) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise NotFoundError("Assignment not found")
    return assignment


def update_assignment(db: Session, assignment: Assignment, data: AssignmentUpdate) -> Assignment:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        # due_at may be cleared with an explicit null; the other fields ignore null.
        if value is None and field != "due_at":
            continue
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment


def delete_assignment(db: Session, assignment: Assignment) -> None:
    db.delete(assignment)
    db.commit()
