"""Shared fixtures.

Tests run against a dedicated PostgreSQL database (``autograder_test``), created on demand.
Each test runs inside a transaction that is rolled back at the end, so tests never see each
other's data.
"""

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, Engine, create_engine, make_url, text
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_background_session_factory, get_db
from app.main import create_app
from app.models import Assignment, Concept, Course, Enrollment, Role, TestCase, User
from app.runner.factory import get_runner
from app.services.course_service import generate_join_code
from tests.fakes import FakeRunner

TEST_DATABASE = "autograder_test"


def database_url(name: str) -> URL:
    return make_url(get_settings().database_url).set(database=name)


def ensure_database(name: str, recreate: bool = False) -> None:
    admin = create_engine(database_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
        )
        if exists and recreate:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            exists = False
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    ensure_database(TEST_DATABASE)
    engine = create_engine(database_url(TEST_DATABASE))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    # Commits inside the code under test become savepoints of the outer transaction.
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def no_submission_interval(monkeypatch):
    """Tests submit in quick succession; the 429 rule is switched on only where it is tested."""
    monkeypatch.setattr(get_settings(), "min_submission_interval_s", 0)


@pytest.fixture
def background_session_factory(db_session: Session) -> Callable[[], Session]:
    """New sessions on the same connection as the test, so background work sees its data."""

    def factory() -> Session:
        return Session(
            bind=db_session.connection(),
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

    return factory


@pytest.fixture
def client(db_session: Session, background_session_factory) -> Iterator[TestClient]:
    app = create_app()

    def request_session() -> Iterator[Session]:
        # A background task may have changed rows through another session: reload them.
        db_session.expire_all()
        yield db_session

    app.dependency_overrides[get_db] = request_session
    app.dependency_overrides[get_background_session_factory] = lambda: background_session_factory
    # Never the real sandbox by accident: a test that submits code sets its own runner.
    app.dependency_overrides[get_runner] = lambda: FakeRunner([])
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_user(db_session: Session) -> Callable[..., User]:
    counter = {"n": 0}

    def _make_user(role: Role = Role.student, password: str | None = None, **overrides) -> User:
        counter["n"] += 1
        fields = {
            "email": f"{role.value}{counter['n']}@example.com",
            "full_name": f"{role.value.title()} {counter['n']}",
            # Argon2 is slow on purpose, so only hash when a test needs to sign in.
            "password_hash": hash_password(password) if password else "!unusable",
            "role": role,
        }
        fields.update(overrides)
        user = User(**fields)
        db_session.add(user)
        db_session.commit()
        return user

    return _make_user


@pytest.fixture
def make_course(db_session: Session, make_user) -> Callable[..., Course]:
    def _make_course(teacher: User | None = None, students: list[User] | None = None, **overrides):
        teacher = teacher or make_user(Role.teacher)
        fields = {
            "title": "Procedural Programming",
            "teacher_id": teacher.id,
            "join_code": generate_join_code(db_session),
        }
        fields.update(overrides)
        course = Course(**fields)
        db_session.add(course)
        db_session.flush()
        for student in students or []:
            db_session.add(Enrollment(user_id=student.id, course_id=course.id))
        db_session.commit()
        return course

    return _make_course


@pytest.fixture
def make_assignment(db_session: Session) -> Callable[..., Assignment]:
    def _make_assignment(course: Course, **overrides) -> Assignment:
        fields = {"title": "Digit sum", "course_id": course.id, "is_published": True}
        fields.update(overrides)
        assignment = Assignment(**fields)
        db_session.add(assignment)
        db_session.commit()
        return assignment

    return _make_assignment


@pytest.fixture
def make_concept(db_session: Session) -> Callable[..., Concept]:
    def _make_concept(course: Course, name: str = "Loops") -> Concept:
        concept = Concept(course_id=course.id, name=name)
        db_session.add(concept)
        db_session.commit()
        return concept

    return _make_concept


@pytest.fixture
def make_test_case(db_session: Session) -> Callable[..., TestCase]:
    def _make_test_case(
        assignment: Assignment, concepts: list[Concept] | None = None, **overrides
    ) -> TestCase:
        fields = {
            "assignment_id": assignment.id,
            "name": "Simple case",
            "input_data": "1234\n",
            "expected_output": "10\n",
            "position": len(assignment.test_cases),
        }
        fields.update(overrides)
        test_case = TestCase(**fields)
        test_case.concepts = concepts or []
        db_session.add(test_case)
        db_session.commit()
        db_session.refresh(assignment)
        return test_case

    return _make_test_case


@pytest.fixture
def auth() -> Callable[[User], dict[str, str]]:
    """Headers that make a request run as the given user."""

    def _auth(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(user)}"}

    return _auth


@pytest.fixture
def teacher(make_user) -> User:
    return make_user(Role.teacher)


@pytest.fixture
def student(make_user) -> User:
    return make_user(Role.student)
