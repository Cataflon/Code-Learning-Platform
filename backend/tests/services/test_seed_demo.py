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
