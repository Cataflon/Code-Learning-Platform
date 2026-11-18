from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment, TestCase
    from app.models.course import Course
    from app.models.user import User


class FileType(enum.StrEnum):
    pdf = "pdf"
    pptx = "pptx"


class MaterialCategory(enum.StrEnum):
    lecture = "lecture"
    lab = "lab"


class Material(Base):
    """A lecture or lab file. The file itself lives in uploads/, never in the database."""

    __tablename__ = "materials"
    __table_args__ = (Index("ix_materials_course_created", "course_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[MaterialCategory] = mapped_column(
        Enum(MaterialCategory, native_enum=False, length=16), default=MaterialCategory.lecture
    )
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, native_enum=False, length=8))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(64), unique=True)  # uuid4 + extension
    preview_filename: Mapped[str | None] = mapped_column(String(64), nullable=True)  # PDF of a PPTX
    size_bytes: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer)
    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship()
    uploader: Mapped[User | None] = relationship()

    @property
    def preview_name(self) -> str:
        """The PDF shown in the viewer: the original, or the PDF converted from the PPTX."""
        return self.preview_filename or self.stored_filename

    @property
    def stored_names(self) -> list[str]:
        """Every file on disk that belongs to this material."""
        return [name for name in (self.stored_filename, self.preview_filename) if name]


class AssignmentMaterial(Base):
    """Where to study for the whole assignment, with optional pages ("12-15, 18")."""

    __tablename__ = "assignment_materials"
    __table_args__ = (Index("ix_assignment_materials_material_id", "material_id"),)

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), primary_key=True
    )
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True
    )
    pages: Mapped[str] = mapped_column(String(200), default="")  # empty = the whole material

    assignment: Mapped[Assignment] = relationship()
    material: Mapped[Material] = relationship(lazy="joined")


class TestCaseMaterial(Base):
    """Where to study when this test fails; feeds the recommendations popup."""

    __tablename__ = "test_case_materials"
    __test__ = False
    __table_args__ = (Index("ix_test_case_materials_material_id", "material_id"),)

    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"), primary_key=True
    )
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True
    )
    pages: Mapped[str] = mapped_column(String(200), default="")

    test_case: Mapped[TestCase] = relationship()
    material: Mapped[Material] = relationship(lazy="joined")
