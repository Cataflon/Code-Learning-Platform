"""Business rules and queries for test cases."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import InvalidDataError, NotFoundError
from app.models import Assignment, Concept, Role, TestCase, User
from app.schemas.assignment import TestCaseCreate, TestCaseUpdate


def _load_concepts(db: Session, course_id: int, concept_ids: list[int]) -> list[Concept]:
    """Concepts must belong to the assignment's course; anything else is a 422."""
    wanted = set(concept_ids)
    if not wanted:
        return []
    concepts = list(
        db.scalars(select(Concept).where(Concept.id.in_(wanted), Concept.course_id == course_id))
    )
    if len(concepts) != len(wanted):
        raise InvalidDataError("Every concept must belong to the same course as the assignment")
    return concepts


def create_test_case(db: Session, assignment: Assignment, data: TestCaseCreate) -> TestCase:
    position = data.position
    if position is None:
        last = db.scalar(
            select(func.max(TestCase.position)).where(TestCase.assignment_id == assignment.id)
        )
        position = 0 if last is None else last + 1
    test_case = TestCase(
        assignment_id=assignment.id,
        position=position,
        **data.model_dump(exclude={"concept_ids", "position"}),
    )
    test_case.concepts = _load_concepts(db, assignment.course_id, data.concept_ids)
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


def list_test_cases(db: Session, assignment: Assignment, viewer: User) -> list[TestCase]:
    """Teacher: every test. Student: public tests only."""
    query = select(TestCase).where(TestCase.assignment_id == assignment.id)
    if viewer.role == Role.student:
        query = query.where(TestCase.is_hidden.is_(False))
    return list(db.scalars(query.order_by(TestCase.position, TestCase.id)))


def get_test_case(db: Session, test_case_id: int) -> TestCase:
    test_case = db.get(TestCase, test_case_id)
    if test_case is None:
        raise NotFoundError("Test case not found")
    return test_case


def update_test_case(db: Session, test_case: TestCase, data: TestCaseUpdate) -> TestCase:
    changes = data.model_dump(exclude_unset=True, exclude={"concept_ids"})
    for field, value in changes.items():
        # hint may be cleared with an explicit null; the other fields ignore null.
        if value is None and field != "hint":
            continue
        setattr(test_case, field, value)
    if data.concept_ids is not None:
        test_case.concepts = _load_concepts(db, test_case.assignment.course_id, data.concept_ids)
    db.commit()
    db.refresh(test_case)
    return test_case


def delete_test_case(db: Session, test_case: TestCase) -> None:
    db.delete(test_case)
    db.commit()
