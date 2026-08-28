"""
SQLAlchemy ORM models mirroring schema.sql.

schema.sql is the source of truth for DDL (run it directly against Postgres
to create tables/constraints/generated columns). These models describe the
same shape so the app can query/insert through the ORM. Generated columns
(weight_kg) are mapped with Computed() so SQLAlchemy excludes them from
INSERT/UPDATE statements — Postgres rejects any explicit value for a
GENERATED ALWAYS column, even NULL.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_unit: Mapped[str] = mapped_column(Text, nullable=False, default="lbs")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (CheckConstraint("preferred_unit IN ('lbs', 'kg')"),)


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    muscle_group: Mapped[str | None] = mapped_column(Text)
    is_custom: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        CheckConstraint("category IN ('push', 'pull', 'legs', 'core', 'other')"),
    )


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session_exercises: Mapped[list["SessionExercise"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionExercise(Base):
    __tablename__ = "session_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(default=0)
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (CheckConstraint("mode IN ('basic', 'advanced')"),)

    session: Mapped["WorkoutSession"] = relationship(back_populates="session_exercises")
    exercise: Mapped["Exercise"] = relationship()
    sets: Mapped[list["ExerciseSet"]] = relationship(
        back_populates="session_exercise", cascade="all, delete-orphan"
    )


class ExerciseSet(Base):
    __tablename__ = "exercise_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("session_exercises.id", ondelete="CASCADE"), nullable=False
    )
    set_number: Mapped[int] = mapped_column(nullable=False)
    reps: Mapped[int] = mapped_column(nullable=False)
    weight_value: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    weight_unit: Mapped[str] = mapped_column(Text, nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        Computed(
            "CASE WHEN weight_unit = 'lbs' THEN ROUND(weight_value * 0.453592, 2) "
            "ELSE weight_value END",
            persisted=True,
        ),
    )
    rpe: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    rest_seconds: Mapped[int | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (CheckConstraint("weight_unit IN ('lbs', 'kg')"),)

    session_exercise: Mapped["SessionExercise"] = relationship(back_populates="sets")


class BodyMetric(Base):
    __tablename__ = "body_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_value: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    weight_unit: Mapped[str] = mapped_column(Text, nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        Computed(
            "CASE WHEN weight_unit = 'lbs' THEN ROUND(weight_value * 0.453592, 2) "
            "ELSE weight_value END",
            persisted=True,
        ),
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        CheckConstraint("weight_unit IN ('lbs', 'kg')"),
        UniqueConstraint("user_id", "metric_date"),
    )

    photos: Mapped[list["ProgressPhoto"]] = relationship(back_populates="body_metric")


class ProgressPhoto(Base):
    __tablename__ = "progress_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body_metric_id: Mapped[int | None] = mapped_column(ForeignKey("body_metrics.id"))
    photo_url: Mapped[str] = mapped_column(Text, nullable=False)
    taken_at: Mapped[datetime] = mapped_column(server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    body_metric: Mapped["BodyMetric | None"] = relationship(back_populates="photos")
