"""
Pydantic request/response schemas.

Naming convention per entity:
- <Entity>Create  — fields accepted on POST (no id, no server-computed columns)
- <Entity>Update  — same fields, all optional, for PATCH
- <Entity>Read    — full shape returned to clients (includes id, computed columns)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

WeightUnit = Literal["lbs", "kg"]
ExerciseCategory = Literal["push", "pull", "legs", "core", "other"]
LoggingMode = Literal["basic", "advanced"]


# ---------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------
class UserCreate(BaseModel):
    name: str
    preferred_unit: WeightUnit = "lbs"


class UserUpdate(BaseModel):
    name: str | None = None
    preferred_unit: WeightUnit | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    preferred_unit: WeightUnit
    created_at: datetime


# ---------------------------------------------------------------------
# EXERCISES
# ---------------------------------------------------------------------
class ExerciseCreate(BaseModel):
    name: str
    category: ExerciseCategory
    muscle_group: str | None = None
    is_custom: bool = True


class ExerciseUpdate(BaseModel):
    name: str | None = None
    category: ExerciseCategory | None = None
    muscle_group: str | None = None


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: ExerciseCategory
    muscle_group: str | None
    is_custom: bool
    created_at: datetime


# ---------------------------------------------------------------------
# WORKOUT SESSIONS
# ---------------------------------------------------------------------
class WorkoutSessionCreate(BaseModel):
    user_id: int
    session_date: date
    notes: str | None = None


class WorkoutSessionUpdate(BaseModel):
    session_date: date | None = None
    notes: str | None = None


class WorkoutSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    session_date: date
    notes: str | None
    created_at: datetime


# ---------------------------------------------------------------------
# SESSION EXERCISES
# ---------------------------------------------------------------------
class SessionExerciseCreate(BaseModel):
    session_id: int
    exercise_id: int
    order_index: int = 0
    mode: LoggingMode


class SessionExerciseUpdate(BaseModel):
    exercise_id: int | None = None
    order_index: int | None = None
    mode: LoggingMode | None = None


class SessionExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    exercise_id: int
    order_index: int
    mode: LoggingMode
    created_at: datetime


# ---------------------------------------------------------------------
# EXERCISE SETS
# ---------------------------------------------------------------------
class ExerciseSetCreate(BaseModel):
    session_exercise_id: int
    set_number: int
    reps: int
    weight_value: Decimal
    weight_unit: WeightUnit
    rpe: Decimal | None = None
    rest_seconds: int | None = None
    notes: str | None = None


class ExerciseSetUpdate(BaseModel):
    set_number: int | None = None
    reps: int | None = None
    weight_value: Decimal | None = None
    weight_unit: WeightUnit | None = None
    rpe: Decimal | None = None
    rest_seconds: int | None = None
    notes: str | None = None


class ExerciseSetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_exercise_id: int
    set_number: int
    reps: int
    weight_value: Decimal
    weight_unit: WeightUnit
    weight_kg: Decimal
    rpe: Decimal | None
    rest_seconds: int | None
    notes: str | None
    created_at: datetime


# ---------------------------------------------------------------------
# BODY METRICS
# ---------------------------------------------------------------------
class BodyMetricCreate(BaseModel):
    user_id: int
    metric_date: date
    weight_value: Decimal
    weight_unit: WeightUnit


class BodyMetricUpdate(BaseModel):
    metric_date: date | None = None
    weight_value: Decimal | None = None
    weight_unit: WeightUnit | None = None


class BodyMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    metric_date: date
    weight_value: Decimal
    weight_unit: WeightUnit
    weight_kg: Decimal
    created_at: datetime


# ---------------------------------------------------------------------
# PROGRESS PHOTOS
# ---------------------------------------------------------------------
class ProgressPhotoCreate(BaseModel):
    user_id: int
    body_metric_id: int | None = None
    photo_url: str
    taken_at: datetime | None = None


class ProgressPhotoUpdate(BaseModel):
    body_metric_id: int | None = None
    photo_url: str | None = None
    taken_at: datetime | None = None


class ProgressPhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    body_metric_id: int | None
    photo_url: str
    taken_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------
# ANALYTICS (read-only aggregates — always expressed in weight_kg;
# the frontend converts to the user's preferred unit for display)
# ---------------------------------------------------------------------
class ExerciseProgressionPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_date: date
    top_weight_kg: Decimal
    volume_kg: Decimal
    sets_count: int


class SessionVolumePoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_date: date
    total_volume_kg: Decimal
