"""Business rules and queries for courses, enrollments and concepts."""

import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.models import Concept, Course, Enrollment, Role, User
from app.schemas.course import ConceptCreate, CourseCreate, CourseUpdate, StudentRead

# No 0/O or 1/I, so a code read aloud or copied by hand is unambiguous.
JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
JOIN_CODE_LENGTH = 8


def generate_join_code(db: Session) -> str:
    while True:
        code = "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(JOIN_CODE_LENGTH))
        taken = db.scalar(select(Course.id).where(Course.join_code == code))
        if taken is None:
            return code


def create_course(db: Session, teacher: User, data: CourseCreate) -> Course:
    course = Course(
        title=data.title,
        description=data.description,
        color=data.color,
        teacher_id=teacher.id,
        join_code=generate_join_code(db),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses_for(db: Session, user: User, limit: int = 50, offset: int = 0) -> list[Course]:
    """Teacher: the courses they own. Student: the courses they are enrolled in."""
    query = select(Course).options(selectinload(Course.assignments))
    if user.role == Role.teacher:
        query = query.where(Course.teacher_id == user.id)
    else:
        query = query.join(Enrollment, Enrollment.course_id == Course.id).where(
            Enrollment.user_id == user.id
        )
    query = query.order_by(Course.created_at, Course.id).limit(limit).offset(offset)
    return list(db.scalars(query))


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise NotFoundError("Course not found")
    return course


def is_enrolled(db: Session, user_id: int, course_id: int) -> bool:
    return db.get(Enrollment, (user_id, course_id)) is not None


def is_member(db: Session, user: User, course: Course) -> bool:
    """A member is the course teacher or an enrolled student."""
    if user.role == Role.teacher:
        return course.teacher_id == user.id
    return is_enrolled(db, user.id, course.id)


def update_course(db: Session, course: Course, data: CourseUpdate) -> Course:
    changes = data.model_dump(exclude_unset=True, exclude={"regenerate_join_code"})
    for field, value in changes.items():
        if value is not None:
            setattr(course, field, value)
    if data.regenerate_join_code:
        course.join_code = generate_join_code(db)
    db.commit()
    db.refresh(course)
    return course


def regenerate_join_code(db: Session, course: Course) -> Course:
    course.join_code = generate_join_code(db)
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()


def join_course(db: Session, student: User, code: str) -> Course:
    if student.role != Role.student:
        raise PermissionDeniedError("Only students can join a course")
    course = db.scalar(select(Course).where(Course.join_code == code.strip().upper()))
    if course is None:
        raise NotFoundError("No course has this code")
    if is_enrolled(db, student.id, course.id):
        raise ConflictError("You are already enrolled in this course")
    db.add(Enrollment(user_id=student.id, course_id=course.id))
    db.commit()
    return course


def leave_course(db: Session, student: User, course: Course) -> None:
    enrollment = db.get(Enrollment, (student.id, course.id))
    if enrollment is None:
        raise NotFoundError("Course not found")
    db.delete(enrollment)
    db.commit()


def list_students(
    db: Session, course: Course, limit: int = 100, offset: int = 0
) -> list[StudentRead]:
    rows = db.execute(
        select(User, Enrollment.created_at)
        .join(Enrollment, Enrollment.user_id == User.id)
        .where(Enrollment.course_id == course.id)
        .order_by(User.full_name, User.id)
        .limit(limit)
        .offset(offset)
    )
    return [
        StudentRead(id=user.id, full_name=user.full_name, email=user.email, enrolled_at=enrolled_at)
        for user, enrolled_at in rows
    ]


def list_concepts(db: Session, course: Course) -> list[Concept]:
    return list(
        db.scalars(select(Concept).where(Concept.course_id == course.id).order_by(Concept.name))
    )


def create_concept(db: Session, course: Course, data: ConceptCreate) -> Concept:
    duplicate = db.scalar(
        select(Concept.id).where(
            Concept.course_id == course.id, func.lower(Concept.name) == data.name.lower()
        )
    )
    if duplicate is not None:
        raise ConflictError("This course already has a concept with this name")
    concept = Concept(course_id=course.id, name=data.name)
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept
