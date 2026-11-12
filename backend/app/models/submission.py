from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment, TestCase
    from app.models.user import User


class SubmissionStatus(enum.StrEnum):
    queued = "queued"
    running = "running"
    done = "done"
    error = "error"


class Verdict(enum.StrEnum):
    passed = "passed"
    wrong_answer = "wrong_answer"
    time_limit = "time_limit"
    memory_limit = "memory_limit"
    runtime_error = "runtime_error"
    internal_error = "internal_error"


class Submission(Base):
    """One attempt. After creation only the status and the results change, never the code."""

    __tablename__ = "submissions"
    __table_args__ = (
        Index(
            "ix_submissions_student_assignment_created",
            "student_id",
            "assignment_id",
            "created_at",
        ),
        Index("ix_submissions_assignment_created", "assignment_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), default="python")
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, native_enum=False, length=16), default=SubmissionStatus.queued
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100, null until done
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_excerpt: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignment: Mapped[Assignment] = relationship()
    student: Mapped[User] = relationship()
    results: Mapped[list[TestResult]] = relationship(
        back_populates="submission", cascade="all, delete-orphan", passive_deletes=True
    )


class TestResult(Base):
    __tablename__ = "test_results"
    __test__ = False
    __table_args__ = (
        UniqueConstraint("submission_id", "test_case_id", name="uq_test_results_submission_test"),
        Index("ix_test_results_submission_id", "submission_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    verdict: Mapped[Verdict] = mapped_column(Enum(Verdict, native_enum=False, length=16))
    actual_output: Mapped[str] = mapped_column(Text, default="")  # truncated
    stderr: Mapped[str] = mapped_column(Text, default="")  # truncated
    runtime_ms: Mapped[int] = mapped_column(Integer, default=0)

    submission: Mapped[Submission] = relationship(back_populates="results")
    test_case: Mapped[TestCase] = relationship()
