"""Demo data for the concept report: one course, three assignments, three students who differ.

* Ana    is good at recursion and weak at lists.
* Bogdan is weak almost everywhere.
* Carmen is good everywhere.

Results are written directly (as if the sandbox had run), with dates in the past, so the
report, the dashboard and the teacher's statistics have something to show without Docker.
Every student also gets an earlier, worse attempt: the report must use the latest one.

Idempotent: running it again changes nothing. Run with ``python -m scripts.seed_demo``.
It also adds two materials to the "Digit sum" course of scripts/seed.py (Step 8): a PDF lecture
linked to the whole assignment and, pages 12-15, to its hidden test, so the recommendations popup
shows up after a wrong submission; and a PPTX lab, only when LibreOffice can convert it.
Step 10 adds the three-week history.
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
from scripts.seed import JOIN_CODE as SEED_JOIN_CODE
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


LECTURE_TITLE = "Lecture 4: Loops and digit extraction"
LAB_TITLE = "Lab 3: Input and output"


def _lecture_pages() -> list[list[str]]:
    pages = [["# Lecture 4", "Loops and digit extraction", "Procedural Programming"]]
    topics = [
        "Recap: for loops",
        "Recap: for loops",
        "Recap: for loops",
        "While loops",
        "While loops",
        "While loops",
        "While loops",
        "Integer division and remainder",
        "Integer division and remainder",
        "Integer division and remainder",
    ]
    for topic in topics:
        pages.append([f"# {topic}", "Notes for this part of the lecture."])
    pages += [
        [
            "# Extracting digits with a while loop",
            "n % 10 gives the last digit",
            "n // 10 removes it",
            "Repeat while n > 0",
            "$ total = 0",
            "$ while n > 0:",
            "$     total += n % 10",
            "$     n //= 10",
        ],
        [
            "# What happens when n is negative",
            "-405 > 0 is false, so the loop never starts",
            "The sum stays at 0",
            "Take abs(n) before the loop",
            "$ n = abs(n)",
            "$ while n > 0:",
        ],
        [
            "# Tracing 1729 step by step",
            "1729: digit 9, then 172",
            "172: digit 2, then 17",
            "17: digit 7, then 1",
            "1: digit 1, then 0 and the loop stops",
        ],
        [
            "# The special case n = 0",
            "The loop does not run, the sum is 0",
            "That is already the right answer",
            "Check it anyway with a test",
        ],
    ]
    for topic in ["Counting and summing"] * 4 + ["Common mistakes"] * 5 + ["Practice problems"] * 4:
        pages.append([f"# {topic}", "Notes for this part of the lecture."])
    return pages  # 28 pages, pages 12-15 explain digit extraction


def seed_materials(db: Session, store=None, converter=None) -> list[str]:
    """Idempotent: adds the two demo materials to the seed course and links them."""
    from app.models import (
        AssignmentMaterial,
        FileType,
        Material,
        MaterialCategory,
        TestCaseMaterial,
    )
    from app.services.material_service import count_pdf_pages
    from app.storage.file_store import get_file_store
    from app.storage.pptx_converter import ConversionError, convert_pptx_to_pdf
    from scripts.demo_pdf import build_pdf

    store = store or get_file_store()
    converter = converter or convert_pptx_to_pdf
    course = db.scalar(select(Course).where(Course.join_code == SEED_JOIN_CODE))
    if course is None:
        return ["Run python -m scripts.seed first: the seed course does not exist."]
    notes = []
    existing = {
        m.title: m for m in db.scalars(select(Material).where(Material.course_id == course.id))
    }
    teacher_id = course.teacher_id

    lecture = existing.get(LECTURE_TITLE)
    if lecture is None:
        source = store.temp_dir() / "lecture-04-loops.pdf"
        source.write_bytes(build_pdf("LECTURE 4 - LOOPS", _lecture_pages()))
        pages = count_pdf_pages(source)
        size = source.stat().st_size
        lecture = Material(
            course_id=course.id,
            title=LECTURE_TITLE,
            category=MaterialCategory.lecture,
            file_type=FileType.pdf,
            original_filename="lecture-04-loops.pdf",
            stored_filename=store.save_file(source, "pdf"),
            size_bytes=size,
            page_count=pages,
            uploaded_by=teacher_id,
        )
        db.add(lecture)
        db.flush()
        notes.append(f"Added '{LECTURE_TITLE}' ({pages} pages)")
        # Index the page text so AI-generated tests can be linked to it (Step 9).
        from app.services.material_service import extract_pages

        extract_pages(db, lecture, store)

    if LAB_TITLE not in existing:
        try:
            from tests.files import pptx_bytes

            work = store.temp_dir()
            source = work / "lab-03-io.pptx"
            source.write_bytes(pptx_bytes(slides=6))
            preview = converter(source, work)
            pages = count_pdf_pages(preview)
            size = source.stat().st_size
            db.add(
                Material(
                    course_id=course.id,
                    title=LAB_TITLE,
                    category=MaterialCategory.lab,
                    file_type=FileType.pptx,
                    original_filename="lab-03-io.pptx",
                    stored_filename=store.save_file(source, "pptx"),
                    preview_filename=store.save_file(preview, "pdf"),
                    size_bytes=size,
                    page_count=pages,
                    uploaded_by=teacher_id,
                )
            )
            notes.append(f"Added '{LAB_TITLE}' ({pages} slides)")
        except (ConversionError, ImportError) as exc:
            notes.append(f"Skipped '{LAB_TITLE}': {exc}")

    assignment = db.scalar(select(Assignment).where(Assignment.course_id == course.id))
    if assignment is not None:
        if db.get(AssignmentMaterial, (assignment.id, lecture.id)) is None:
            db.add(
                AssignmentMaterial(assignment_id=assignment.id, material_id=lecture.id, pages="")
            )
        hidden = next((t for t in assignment.test_cases if t.is_hidden), None)
        if hidden is not None and db.get(TestCaseMaterial, (hidden.id, lecture.id)) is None:
            db.add(TestCaseMaterial(test_case_id=hidden.id, material_id=lecture.id, pages="12-15"))
    db.commit()
    return notes


def main() -> None:
    with get_session_factory()() as db:
        course = seed_demo(db)
        for note in seed_materials(db):
            print(note)
        print(f"Demo course ready: '{course.title}', join code {course.join_code}")
        print("Students: " + ", ".join(email for email, _, _ in STUDENTS))
        print(f"Teacher: {TEACHER_EMAIL}; password for every account: {SEED_PASSWORD}")


if __name__ == "__main__":
    main()
