from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.user import User

# Fixed palette; the frontend maps each name to a Tailwind color.
COURSE_COLORS = ("indigo", "blue", "purple", "green", "amber", "rose")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    join_code: Mapped[str] = mapped_column(String(8), unique=True)
    color: Mapped[str] = mapped_column(String(16), default=COURSE_COLORS[0])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    teacher: Mapped[User] = relationship(lazy="joined")
    assignments: Mapped[list[Assignment]] = relationship(
        back_populates="course", cascade="all, delete-orphan", passive_deletes=True
    )
    enrollments: Mapped[list[Enrollment]] = relationship(
        back_populates="course", cascade="all, delete-orphan", passive_deletes=True
    )
    concepts: Mapped[list[Concept]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Concept.name",
    )

    @property
    def teacher_name(self) -> str:
        return self.teacher.full_name


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (Index("ix_enrollments_course_id", "course_id"),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship(back_populates="enrollments")
    user: Mapped[User] = relationship()


class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (UniqueConstraint("course_id", "name", name="uq_concepts_course_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))

    course: Mapped[Course] = relationship(back_populates="concepts")
