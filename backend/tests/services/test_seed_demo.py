"""The demo data must tell three different stories in the concept report."""

from sqlalchemy import func, select

from app.models import Course, User
from app.services import report_service
from scripts.seed_demo import seed_demo


def levels_of(db, email, course):
    student = db.scalar(select(User).where(User.email == email))
    report = report_service.student_concept_report(db, student, course)
    return {concept.concept: concept.level for concept in report.concepts}


def test_seed_demo_gives_three_different_profiles_and_is_idempotent(db_session):
    course = seed_demo(db_session)
    again = seed_demo(db_session)

    assert again.id == course.id
    assert (
        db_session.scalar(select(func.count()).select_from(Course).where(Course.id == course.id))
        == 1
    )

    ana = levels_of(db_session, "ana.recursion@student.utcluj.ro", course)
    bogdan = levels_of(db_session, "bogdan.weak@student.utcluj.ro", course)
    carmen = levels_of(db_session, "carmen.strong@student.utcluj.ro", course)

    assert ana["Recursion"] == "mastered"
    assert ana["Lists"] == "review"
    assert set(carmen.values()) == {"mastered"}  # the latest attempt is perfect
    assert sum(1 for level in bogdan.values() if level == "review") >= 3
    assert ana != bogdan != carmen


def test_seed_materials_links_the_lecture_to_the_hidden_test(
    db_session, file_store, fake_converter
):
    from app.models import Material, TestCaseMaterial
    from scripts.seed import seed
    from scripts.seed_demo import LECTURE_TITLE, seed_materials

    seed(db_session)

    notes = seed_materials(db_session, store=file_store, converter=fake_converter)
    again = seed_materials(db_session, store=file_store, converter=fake_converter)

    lecture = db_session.scalar(select(Material).where(Material.title == LECTURE_TITLE))
    assert lecture.page_count == 28
    assert len(notes) == 2 and again == []
    link = db_session.scalar(
        select(TestCaseMaterial).where(TestCaseMaterial.material_id == lecture.id)
    )
    assert link.pages == "12-15"
    assert file_store.path(lecture.stored_filename).read_bytes().startswith(b"%PDF-")


def test_seed_history_gives_eight_students_and_three_weeks_of_attempts(db_session):
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import func, select

    from app.models import Enrollment, Submission
    from scripts.seed_demo import seed_history

    course = seed_demo(db_session)
    added = seed_history(db_session, course)

    assert added > 0
    assert seed_history(db_session, course) == 0  # idempotent
    students = db_session.scalar(
        select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course.id)
    )
    oldest = db_session.scalar(
        select(func.min(Submission.created_at)).where(
            Submission.assignment_id.in_([a.id for a in course.assignments])
        )
    )
    assert students == 8
    assert oldest < datetime.now(UTC) - timedelta(days=14)
