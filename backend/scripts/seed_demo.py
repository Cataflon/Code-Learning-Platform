"""Demo data for the concept report: one course, three assignments, three students who differ.

* Ana    is good at recursion and weak at lists.
* Bogdan is weak almost everywhere.
* Carmen is good everywhere.

Results are written directly (as if the sandbox had run), with dates in the past, so the
report, the dashboard and the teacher's statistics have something to show without Docker.
Every student also gets an earlier, worse attempt: the report must use the latest one.

Idempotent: running it again changes nothing. Run with ``python -m scripts.seed_demo``.
Step 8 adds the demo materials and Step 10 the three-week history.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.models import (
    Assignment,
    Concept,
    Course,
    Enrollment,
    Role,
    Submission,
    SubmissionStatus,
    TestCase,
    TestResult,
    Verdict,
)
from app.services.scoring import compute_score, count_passed
from scripts.seed import SEED_PASSWORD, TEACHER_EMAIL, get_or_create_user

JOIN_CODE = "DEMOPY26"
CONCEPTS = ["Input and output", "Loops", "Recursion", "Lists", "Edge cases"]

# (title, days until due, [(test name, input, expected, hidden, concepts)])
ASSIGNMENTS = [
    (
        "Factorial",
        -3,
        [
            ("Small number", "5\n", "120\n", False, ["Recursion"]),
            ("One", "1\n", "1\n", False, ["Recursion", "Edge cases"]),
            ("Zero", "0\n", "1\n", True, ["Recursion", "Edge cases"]),
            ("Twenty", "20\n", "2432902008176640000\n", False, ["Recursion"]),
        ],
    ),
    (
        "List statistics",
        2,
        [
            ("Three numbers", "3\n4 1 7\n", "1 7 4.0\n", False, ["Lists", "Input and output"]),
            ("One number", "1\n9\n", "9 9 9.0\n", False, ["Lists", "Edge cases"]),
            ("Negatives", "3\n-2 -9 5\n", "-9 5 -2.0\n", True, ["Lists"]),
            ("Long list", "6\n1 2 3 4 5 6\n", "1 6 3.5\n", False, ["Lists", "Loops"]),
        ],
    ),
    (
        "Countdown",
        6,
        [
            ("From three", "3\n", "3\n2\n1\n0\n", False, ["Loops", "Input and output"]),
            ("From zero", "0\n", "0\n", False, ["Loops", "Edge cases"]),
            ("From ten", "10\n", "10\n9\n8\n7\n6\n5\n4\n3\n2\n1\n0\n", True, ["Loops"]),
        ],
    ),
]

# Which concepts each student gets wrong in the latest attempt. A test fails when any of
# its concepts is weak; the first attempt also fails the last test of every assignment.
STUDENTS = [
    ("ana.recursion@student.utcluj.ro", "Ana Pop", {"Lists"}),
    ("bogdan.weak@student.utcluj.ro", "Bogdan Rus", {"Recursion", "Lists", "Loops", "Edge cases"}),
    ("carmen.strong@student.utcluj.ro", "Carmen Dan", set()),
]

DEMO_CODE = "# demo submission\nprint(input())\n"


def _verdicts(tests: list[TestCase], weak: set[str], first_attempt: bool) -> list[Verdict]:
    verdicts = []
    for index, test in enumerate(tests):
        names = {concept.name for concept in test.concepts}
        failed = bool(names & weak) or (first_attempt and index == len(tests) - 1)
        verdicts.append(Verdict.wrong_answer if failed else Verdict.passed)
    return verdicts


def _store_submission(
    db: Session, student_id: int, assignment: Assignment, verdicts: list[Verdict], when: datetime
) -> None:
    tests = list(assignment.test_cases)
    submission = Submission(
        assignment_id=assignment.id,
        student_id=student_id,
        code=DEMO_CODE,
        status=SubmissionStatus.done,
        total_count=len(tests),
        created_at=when,
        started_at=when,
        finished_at=when + timedelta(seconds=3),
    )
    db.add(submission)
    db.flush()
    by_test = {}
    for test, verdict in zip(tests, verdicts, strict=True):
        by_test[test.id] = verdict
        db.add(
            TestResult(
                submission_id=submission.id,
                test_case_id=test.id,
                verdict=verdict,
                actual_output=test.expected_output if verdict == Verdict.passed else "0\n",
                runtime_ms=30,
            )
        )
    submission.score = compute_score(by_test, {test.id: test.weight for test in tests})
    submission.passed_count = count_passed(by_test.values())


def seed_demo(db: Session) -> Course:
    existing = db.scalar(select(Course).where(Course.join_code == JOIN_CODE))
    if existing is not None:
        return existing

    teacher = get_or_create_user(db, TEACHER_EMAIL, "Dr. Maria Ionescu", Role.teacher)
    course = Course(
        title="Python Basics (demo)",
        description="Demo course for the concept report.",
        teacher_id=teacher.id,
        join_code=JOIN_CODE,
        color="blue",
    )
    db.add(course)
    db.flush()
    concepts = {name: Concept(course_id=course.id, name=name) for name in CONCEPTS}
    db.add_all(concepts.values())
    db.flush()

    now = datetime.now(UTC)
    assignments = []
    for title, due_in_days, tests in ASSIGNMENTS:
        assignment = Assignment(
            course_id=course.id,
            title=title,
            description=f"Demo assignment: {title.lower()}.",
            is_published=True,
            due_at=(now + timedelta(days=due_in_days)).replace(hour=23, minute=59, second=0),
        )
        db.add(assignment)
        db.flush()
        for position, (name, stdin, expected, hidden, tags) in enumerate(tests):
            db.add(
                TestCase(
                    assignment_id=assignment.id,
                    name=name,
                    input_data=stdin,
                    expected_output=expected,
                    is_hidden=hidden,
                    position=position,
                    concepts=[concepts[tag] for tag in tags],
                )
            )
        db.flush()
        db.refresh(assignment)
        assignments.append(assignment)

    for index, (email, full_name, weak) in enumerate(STUDENTS):
        student = get_or_create_user(db, email, full_name, Role.student)
        db.add(Enrollment(user_id=student.id, course_id=course.id))
        for number, assignment in enumerate(assignments):
            first = now - timedelta(days=4 - number, hours=index + 2)
            tests = list(assignment.test_cases)
            _store_submission(db, student.id, assignment, _verdicts(tests, weak, True), first)
            latest = first + timedelta(hours=1)
            _store_submission(db, student.id, assignment, _verdicts(tests, weak, False), latest)
    db.commit()
    return course


def main() -> None:
    with get_session_factory()() as db:
        course = seed_demo(db)
        print(f"Demo course ready: '{course.title}', join code {course.join_code}")
        print("Students: " + ", ".join(email for email, _, _ in STUDENTS))
        print(f"Teacher: {TEACHER_EMAIL}; password for every account: {SEED_PASSWORD}")


if __name__ == "__main__":
    main()
