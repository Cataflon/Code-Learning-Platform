from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.generation import ReviewStatus, TestSource

if TYPE_CHECKING:
    from app.models.course import Concept, Course


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")  # Markdown
    language: Mapped[str] = mapped_column(String(16), default="python")
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=128)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    max_submissions: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship(back_populates="assignments")
    test_cases: Mapped[list[TestCase]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TestCase.position, TestCase.id",
    )

    @property
    def course_title(self) -> str:
        return self.course.title

    @property
    def status(self) -> str:
        """Displayed state: draft until published, open until the deadline, closed after it."""
        if not self.is_published:
            return "draft"
        if self.due_at is not None and self.due_at <= datetime.now(UTC):
            return "closed"
        return "open"

    @property
    def approved_tests(self) -> list[TestCase]:
        """The tests that count: evaluation and students only ever see these (Step 9)."""
        return [test for test in self.test_cases if test.review_status == ReviewStatus.approved]

    @property
    def test_count(self) -> int:
        return len(self.approved_tests)

    @property
    def hidden_test_count(self) -> int:
        return sum(1 for test in self.approved_tests if test.is_hidden)

    @property
    def draft_test_count(self) -> int:
        """AI-generated tests still waiting for the teacher's review."""
        return len(self.test_cases) - len(self.approved_tests)


# Pure link table for the many-to-many relation between tests and concepts.
test_case_concepts = Table(
    "test_case_concepts",
    Base.metadata,
    Column("test_case_id", ForeignKey("test_cases.id", ondelete="CASCADE"), primary_key=True),
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)


class TestCase(Base):
    __tablename__ = "test_cases"
    __test__ = False  # not a pytest test class, despite the name

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    input_data: Mapped[str] = mapped_column(Text, default="")
    expected_output: Mapped[str] = mapped_column(Text, default="")
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    position: Mapped[int] = mapped_column(Integer, default=0)
    hint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Step 9: tests written by the AI generator start as drafts and count only once approved.
    source: Mapped[TestSource] = mapped_column(
        Enum(TestSource, native_enum=False, length=16),
        default=TestSource.manual,
        server_default=TestSource.manual.value,
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, native_enum=False, length=16),
        default=ReviewStatus.approved,
        server_default=ReviewStatus.approved.value,
    )
    generation_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True
    )
    ai_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When the AI wrote the solution, a second independent solution runs too; if it printed
    # something else on this input, its output is kept here so the teacher can decide.
    ai_check_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignment: Mapped[Assignment] = relationship(back_populates="test_cases")
    concepts: Mapped[list[Concept]] = relationship(
        secondary=test_case_concepts, order_by="Concept.name", lazy="selectin"
    )
