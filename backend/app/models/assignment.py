from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

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
    def test_count(self) -> int:
        return len(self.test_cases)

    @property
    def hidden_test_count(self) -> int:
        return sum(1 for test in self.test_cases if test.is_hidden)


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

    assignment: Mapped[Assignment] = relationship(back_populates="test_cases")
    concepts: Mapped[list[Concept]] = relationship(
        secondary=test_case_concepts, order_by="Concept.name", lazy="selectin"
    )
