from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/exercise-progression", response_model=list[schemas.ExerciseProgressionPoint])
def exercise_progression(
    user_id: int,
    exercise_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(
            models.WorkoutSession.session_date,
            func.max(models.ExerciseSet.weight_kg).label("top_weight_kg"),
            func.sum(models.ExerciseSet.reps * models.ExerciseSet.weight_kg).label("volume_kg"),
            func.count(models.ExerciseSet.id).label("sets_count"),
        )
        .join(
            models.SessionExercise,
            models.SessionExercise.session_id == models.WorkoutSession.id,
        )
        .join(
            models.ExerciseSet,
            models.ExerciseSet.session_exercise_id == models.SessionExercise.id,
        )
        .where(
            models.WorkoutSession.user_id == user_id,
            models.SessionExercise.exercise_id == exercise_id,
        )
        .group_by(models.WorkoutSession.session_date)
        .order_by(models.WorkoutSession.session_date)
    )
    if date_from is not None:
        stmt = stmt.where(models.WorkoutSession.session_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(models.WorkoutSession.session_date <= date_to)
    return db.execute(stmt).all()


@router.get("/session-volume", response_model=list[schemas.SessionVolumePoint])
def session_volume(
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(
            models.WorkoutSession.session_date,
            func.sum(models.ExerciseSet.reps * models.ExerciseSet.weight_kg).label(
                "total_volume_kg"
            ),
        )
        .join(
            models.SessionExercise,
            models.SessionExercise.session_id == models.WorkoutSession.id,
        )
        .join(
            models.ExerciseSet,
            models.ExerciseSet.session_exercise_id == models.SessionExercise.id,
        )
        .where(models.WorkoutSession.user_id == user_id)
        .group_by(models.WorkoutSession.session_date)
        .order_by(models.WorkoutSession.session_date)
    )
    if date_from is not None:
        stmt = stmt.where(models.WorkoutSession.session_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(models.WorkoutSession.session_date <= date_to)
    return db.execute(stmt).all()
