import pytest
from sqlalchemy import func, select

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.models import Assignment, Concept, Enrollment, Role, TestCase
from app.schemas.assignment import TestCaseCreate
from app.schemas.course import ConceptCreate, CourseCreate
from app.services import course_service, test_case_service


def test_create_course_generates_unique_join_code(db_session, teacher):
    first = course_service.create_course(db_session, teacher, CourseCreate(title="A"))
    second = course_service.create_course(db_session, teacher, CourseCreate(title="B"))

    assert len(first.join_code) == 8
    assert first.join_code != second.join_code


def test_join_course_enrolls_student(db_session, make_course, student):
    course = make_course()

    joined = course_service.join_course(db_session, student, course.join_code.lower())

    assert joined.id == course.id
    assert course_service.is_enrolled(db_session, student.id, course.id)


def test_join_course_twice_raises_conflict(db_session, make_course, student):
    course = make_course()
    course_service.join_course(db_session, student, course.join_code)

    with pytest.raises(ConflictError):
        course_service.join_course(db_session, student, course.join_code)


def test_join_course_with_unknown_code_raises_not_found(db_session, student):
    with pytest.raises(NotFoundError):
        course_service.join_course(db_session, student, "NOPE0000")


def test_list_courses_for_depends_on_role(db_session, make_course, make_user):
    teacher, other_teacher = make_user(Role.teacher), make_user(Role.teacher)
    student = make_user(Role.student)
    mine = make_course(teacher, students=[student])
    make_course(other_teacher)

    assert [c.id for c in course_service.list_courses_for(db_session, teacher)] == [mine.id]
    assert [c.id for c in course_service.list_courses_for(db_session, student)] == [mine.id]
    assert len(course_service.list_courses_for(db_session, other_teacher)) == 1


def test_regenerate_join_code_invalidates_the_old_one(db_session, make_course, student):
    course = make_course()
    old_code = course.join_code

    course_service.regenerate_join_code(db_session, course)

    assert course.join_code != old_code
    with pytest.raises(NotFoundError):
        course_service.join_course(db_session, student, old_code)


def test_delete_course_cascades_to_everything_below(
    db_session, make_course, make_assignment, make_concept, make_test_case, student
):
    course = make_course(students=[student])
    assignment = make_assignment(course)
    make_test_case(assignment, concepts=[make_concept(course)])

    course_service.delete_course(db_session, course)
    db_session.expire_all()

    for model in (Assignment, TestCase, Concept, Enrollment):
        assert db_session.scalar(select(func.count()).select_from(model)) == 0


def test_create_concept_rejects_duplicate_name_ignoring_case(db_session, make_course):
    course = make_course()
    course_service.create_concept(db_session, course, ConceptCreate(name="Loops"))

    with pytest.raises(ConflictError):
        course_service.create_concept(db_session, course, ConceptCreate(name="loops"))


def test_test_case_rejects_concept_from_another_course(
    db_session, make_course, make_assignment, make_concept
):
    assignment = make_assignment(make_course())
    foreign_concept = make_concept(make_course(), "Recursion")

    with pytest.raises(InvalidDataError):
        test_case_service.create_test_case(
            db_session, assignment, TestCaseCreate(name="t", concept_ids=[foreign_concept.id])
        )


def test_test_cases_are_appended_in_order(db_session, make_course, make_assignment):
    assignment = make_assignment(make_course())

    first = test_case_service.create_test_case(db_session, assignment, TestCaseCreate(name="a"))
    second = test_case_service.create_test_case(db_session, assignment, TestCaseCreate(name="b"))

    assert (first.position, second.position) == (0, 1)
