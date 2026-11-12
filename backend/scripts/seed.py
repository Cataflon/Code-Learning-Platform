"""Small development seed: one teacher, two students, one course, one assignment with five tests.

Idempotent: running it twice leaves the same data. Run with ``python -m scripts.seed``.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models import Assignment, Concept, Course, Enrollment, Role, TestCase, User

SEED_PASSWORD = "parola123"
TEACHER_EMAIL = "maria.ionescu@utcluj.ro"
STUDENT_EMAILS = ("andrei.pop@student.utcluj.ro", "elena.matei@student.utcluj.ro")
COURSE_TITLE = "Procedural Programming"
JOIN_CODE = "PP4K7MAB"


def get_or_create_user(db: Session, email: str, full_name: str, role: Role) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None and not user.password_hash.startswith("$argon2"):
        user.password_hash = hash_password(SEED_PASSWORD)  # repair a pre-auth placeholder
    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            password_hash=hash_password(SEED_PASSWORD),
        )
        db.add(user)
        db.flush()
    return user


def seed(db: Session) -> Course:
    teacher = get_or_create_user(db, TEACHER_EMAIL, "Dr. Maria Ionescu", Role.teacher)
    students = [
        get_or_create_user(db, STUDENT_EMAILS[0], "Andrei Pop", Role.student),
        get_or_create_user(db, STUDENT_EMAILS[1], "Elena Matei", Role.student),
    ]

    course = db.scalar(select(Course).where(Course.join_code == JOIN_CODE))
    if course is not None:
        db.commit()
        return course

    course = Course(
        title=COURSE_TITLE,
        description="Introductory programming course.",
        teacher_id=teacher.id,
        join_code=JOIN_CODE,
        color="indigo",
    )
    db.add(course)
    db.flush()
    for student in students:
        db.add(Enrollment(user_id=student.id, course_id=course.id))

    concepts = {
        name: Concept(course_id=course.id, name=name)
        for name in ("Loops", "Edge cases", "Negative numbers")
    }
    db.add_all(concepts.values())

    assignment = Assignment(
        course_id=course.id,
        title="Digit sum",
        description=(
            "Read an integer from standard input and print the sum of its digits. "
            "For negative numbers, ignore the sign."
        ),
        is_published=True,
    )
    db.add(assignment)
    db.flush()

    tests = [
        ("Simple case", "1234\n", "10\n", False, 2, ["Loops"], None),
        ("Single digit", "7\n", "7\n", False, 2, ["Loops"], None),
        ("Zero", "0\n", "0\n", False, 2, ["Edge cases"], None),
        ("Large number", "999999999999999999\n", "162\n", False, 2, ["Edge cases"], None),
        (
            "Hidden test",
            "-9075\n",
            "21\n",
            True,
            2,
            ["Negative numbers"],
            "Check what happens to the sign. Try -123 locally.",
        ),
    ]
    for position, (name, stdin, expected, hidden, weight, tags, hint) in enumerate(tests):
        db.add(
            TestCase(
                assignment_id=assignment.id,
                name=name,
                input_data=stdin,
                expected_output=expected,
                is_hidden=hidden,
                weight=weight,
                position=position,
                hint=hint,
                concepts=[concepts[tag] for tag in tags],
            )
        )
    db.commit()
    return course


def main() -> None:
    with get_session_factory()() as db:
        course = seed(db)
        print(f"Seed ready: course '{course.title}', join code {course.join_code}")
        print(f"Teacher: {TEACHER_EMAIL} / students: {', '.join(STUDENT_EMAILS)}")
        print(f"Password for all seeded accounts: {SEED_PASSWORD}")


if __name__ == "__main__":
    main()
