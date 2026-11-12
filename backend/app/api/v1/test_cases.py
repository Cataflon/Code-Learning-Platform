from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession, MemberAssignment, OwnedAssignment, OwnedTestCase
from app.models import Role
from app.schemas.assignment import (
    TestCaseCreate,
    TestCasePublicRead,
    TestCaseRead,
    TestCaseUpdate,
)
from app.services import test_case_service

router = APIRouter(tags=["test-cases"])


@router.get(
    "/assignments/{assignment_id}/test-cases",
    response_model=list[TestCaseRead] | list[TestCasePublicRead],
)
def list_test_cases(assignment: MemberAssignment, db: DbSession, user: CurrentUser):
    test_cases = test_case_service.list_test_cases(db, assignment, user)
    schema = TestCaseRead if user.role == Role.teacher else TestCasePublicRead
    return [schema.model_validate(test_case) for test_case in test_cases]


@router.post(
    "/assignments/{assignment_id}/test-cases",
    response_model=TestCaseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_test_case(data: TestCaseCreate, assignment: OwnedAssignment, db: DbSession):
    return test_case_service.create_test_case(db, assignment, data)


@router.patch("/test-cases/{test_case_id}", response_model=TestCaseRead)
def update_test_case(data: TestCaseUpdate, test_case: OwnedTestCase, db: DbSession):
    return test_case_service.update_test_case(db, test_case, data)


@router.delete("/test-cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(test_case: OwnedTestCase, db: DbSession) -> None:
    test_case_service.delete_test_case(db, test_case)
