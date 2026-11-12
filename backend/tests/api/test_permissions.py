"""The permission matrix: one parametrized test, one line per (actor, method, path).

Actors:
  anonymous      no token
  owner          the teacher of the course
  other_teacher  a teacher of a different course
  member         a student enrolled in the course
  classmate      another student enrolled in the same course
  outsider       a student who is not enrolled

Every new route adds lines here.
"""

import pytest

from app.models import Role, Submission

API = "/api/v1"

COURSE = "/courses/{course}"
ASSIGNMENT = "/assignments/{assignment}"
DRAFT = "/assignments/{draft}"
TEST_CASE = "/test-cases/{test_case}"
SUBMISSION = "/submissions/{submission}"

NEW_COURSE = {"title": "New course"}
NEW_ASSIGNMENT = {"title": "New assignment"}
NEW_TEST = {"name": "New test"}
NEW_CONCEPT = {"name": "New concept"}
CODE = {"code": "print(1)"}

MATRIX = [
    # --- profile
    ("anonymous", "GET", "/users/me", None, 401),
    ("member", "GET", "/users/me", None, 200),
    ("anonymous", "PATCH", "/users/me", {"full_name": "X"}, 401),
    # --- courses
    ("anonymous", "GET", "/courses", None, 401),
    ("member", "GET", "/courses", None, 200),
    ("anonymous", "POST", "/courses", NEW_COURSE, 401),
    ("member", "POST", "/courses", NEW_COURSE, 403),
    ("owner", "POST", "/courses", NEW_COURSE, 201),
    ("owner", "GET", COURSE, None, 200),
    ("member", "GET", COURSE, None, 200),
    ("outsider", "GET", COURSE, None, 404),
    ("other_teacher", "GET", COURSE, None, 404),
    ("member", "PATCH", COURSE, {"title": "Hacked"}, 403),
    ("other_teacher", "PATCH", COURSE, {"title": "Hacked"}, 404),
    ("owner", "PATCH", COURSE, {"title": "Renamed"}, 200),
    ("member", "DELETE", COURSE, None, 403),
    ("other_teacher", "DELETE", COURSE, None, 404),
    ("owner", "DELETE", COURSE, None, 204),
    ("owner", "POST", "/courses/join", {"join_code": "WHATEVER"}, 403),
    ("member", "GET", COURSE + "/students", None, 403),
    ("other_teacher", "GET", COURSE + "/students", None, 404),
    ("owner", "GET", COURSE + "/students", None, 200),
    ("member", "POST", COURSE + "/join-code", None, 403),
    ("other_teacher", "POST", COURSE + "/join-code", None, 404),
    ("owner", "POST", COURSE + "/join-code", None, 200),
    ("owner", "DELETE", COURSE + "/enrollment", None, 403),
    ("outsider", "DELETE", COURSE + "/enrollment", None, 404),
    ("member", "DELETE", COURSE + "/enrollment", None, 204),
    # --- concepts
    ("member", "GET", COURSE + "/concepts", None, 200),
    ("outsider", "GET", COURSE + "/concepts", None, 404),
    ("member", "POST", COURSE + "/concepts", NEW_CONCEPT, 403),
    ("other_teacher", "POST", COURSE + "/concepts", NEW_CONCEPT, 404),
    ("owner", "POST", COURSE + "/concepts", NEW_CONCEPT, 201),
    # --- assignments
    ("member", "GET", COURSE + "/assignments", None, 200),
    ("outsider", "GET", COURSE + "/assignments", None, 404),
    ("member", "POST", COURSE + "/assignments", NEW_ASSIGNMENT, 403),
    ("other_teacher", "POST", COURSE + "/assignments", NEW_ASSIGNMENT, 404),
    ("owner", "POST", COURSE + "/assignments", NEW_ASSIGNMENT, 201),
    ("anonymous", "GET", ASSIGNMENT, None, 401),
    ("member", "GET", ASSIGNMENT, None, 200),
    ("outsider", "GET", ASSIGNMENT, None, 404),
    ("other_teacher", "GET", ASSIGNMENT, None, 404),
    ("member", "GET", DRAFT, None, 404),  # students cannot see drafts
    ("owner", "GET", DRAFT, None, 200),
    ("member", "PATCH", ASSIGNMENT, {"title": "Hacked"}, 403),
    ("other_teacher", "PATCH", ASSIGNMENT, {"title": "Hacked"}, 404),
    ("owner", "PATCH", ASSIGNMENT, {"is_published": False}, 200),
    ("member", "DELETE", ASSIGNMENT, None, 403),
    ("owner", "DELETE", ASSIGNMENT, None, 204),
    # --- test cases
    ("member", "GET", ASSIGNMENT + "/test-cases", None, 200),
    ("outsider", "GET", ASSIGNMENT + "/test-cases", None, 404),
    ("member", "POST", ASSIGNMENT + "/test-cases", NEW_TEST, 403),
    ("other_teacher", "POST", ASSIGNMENT + "/test-cases", NEW_TEST, 404),
    ("owner", "POST", ASSIGNMENT + "/test-cases", NEW_TEST, 201),
    ("member", "PATCH", TEST_CASE, {"weight": 9}, 403),
    ("other_teacher", "PATCH", TEST_CASE, {"weight": 9}, 404),
    ("owner", "PATCH", TEST_CASE, {"weight": 9}, 200),
    ("member", "DELETE", TEST_CASE, None, 403),
    ("other_teacher", "DELETE", TEST_CASE, None, 404),
    ("owner", "DELETE", TEST_CASE, None, 204),
    # --- submissions
    ("anonymous", "POST", ASSIGNMENT + "/submissions", CODE, 401),
    ("owner", "POST", ASSIGNMENT + "/submissions", CODE, 403),
    ("outsider", "POST", ASSIGNMENT + "/submissions", CODE, 404),
    ("member", "POST", DRAFT + "/submissions", CODE, 404),
    ("member", "POST", ASSIGNMENT + "/submissions", CODE, 202),
    ("member", "GET", ASSIGNMENT + "/submissions", None, 200),
    ("owner", "GET", ASSIGNMENT + "/submissions", None, 200),
    ("outsider", "GET", ASSIGNMENT + "/submissions", None, 404),
    ("other_teacher", "GET", ASSIGNMENT + "/submissions", None, 404),
    ("anonymous", "GET", SUBMISSION, None, 401),
    ("member", "GET", SUBMISSION, None, 200),  # the author
    ("owner", "GET", SUBMISSION, None, 200),
    ("classmate", "GET", SUBMISSION, None, 404),
    ("outsider", "GET", SUBMISSION, None, 404),
    ("other_teacher", "GET", SUBMISSION, None, 404),
]


@pytest.fixture
def world(db_session, make_user, make_course, make_assignment, make_test_case):
    """One course with every kind of actor around it."""
    owner, other_teacher = make_user(Role.teacher), make_user(Role.teacher)
    member, outsider = make_user(Role.student), make_user(Role.student)
    classmate = make_user(Role.student)
    course = make_course(owner, students=[member, classmate])
    make_course(other_teacher)
    assignment = make_assignment(course)
    draft = make_assignment(course, title="Draft", is_published=False)
    test_case = make_test_case(assignment)
    submission = Submission(assignment_id=assignment.id, student_id=member.id, code="print(1)")
    db_session.add(submission)
    db_session.commit()
    return {
        "actors": {
            "owner": owner,
            "other_teacher": other_teacher,
            "member": member,
            "classmate": classmate,
            "outsider": outsider,
        },
        "ids": {
            "course": course.id,
            "assignment": assignment.id,
            "draft": draft.id,
            "test_case": test_case.id,
            "submission": submission.id,
        },
    }


@pytest.mark.parametrize(
    ("actor", "method", "path", "body", "expected"),
    MATRIX,
    ids=[f"{actor} {method} {path} -> {status}" for actor, method, path, _, status in MATRIX],
)
def test_permission_matrix(client, auth, world, actor, method, path, body, expected):
    headers = {} if actor == "anonymous" else auth(world["actors"][actor])
    url = API + path.format(**world["ids"])

    response = client.request(method, url, json=body, headers=headers)

    assert response.status_code == expected, response.text
