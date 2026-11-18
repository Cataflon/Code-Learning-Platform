from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Computed,
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
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.submission import SubmissionStatus

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.material import Material


class TestSource(enum.StrEnum):
    __test__ = False

    manual = "manual"
    ai = "ai"


class ReviewStatus(enum.StrEnum):
    approved = "approved"
    draft = "draft"


class GenerationJob(Base):
    """One request to generate tests with AI for an assignment (Step 9).

    The status reuses the submission lifecycle: queued -> running -> done | error.
    ``tests_proposed`` stays empty until the model answered and ``tests_kept`` until the
    sandbox ran, which is how the page shows the phase without a column of its own.
    """

    __tablename__ = "generation_jobs"
    __table_args__ = (
        Index("ix_generation_jobs_assignment_created", "assignment_id", "created_at"),
        Index("ix_generation_jobs_requested_created", "requested_by", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, native_enum=False, length=16), default=SubmissionStatus.queued
    )
    reference_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(64))
    tests_requested: Mapped[int] = mapped_column(Integer, default=8)
    tests_proposed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tests_kept: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignment: Mapped[Assignment] = relationship()


class MaterialPage(Base):
    """The text of one page of a material, indexed for full-text search (decision D27)."""

    __tablename__ = "material_pages"
    __table_args__ = (
        UniqueConstraint("material_id", "page_no", name="uq_material_pages_material_page"),
        Index("ix_material_pages_tsv", "tsv", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"))
    page_no: Mapped[int] = mapped_column(Integer)  # 1 = first page of the PDF or of the preview
    text: Mapped[str] = mapped_column(Text)
    tsv: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('simple', text)", persisted=True)
    )

    material: Mapped[Material] = relationship()
