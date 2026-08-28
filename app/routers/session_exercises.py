from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/session-exercises", tags=["session exercises"])


@router.post("", response_model=schemas.SessionExerciseRead, status_code=201)
def create_session_exercise(
    payload: schemas.SessionExerciseCreate, db: Session = Depends(get_db)
):
    if db.get(models.WorkoutSession, payload.session_id) is None:
        raise HTTPException(status_code=404, detail="Workout session not found")
    if db.get(models.Exercise, payload.exercise_id) is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    session_exercise = models.SessionExercise(**payload.model_dump())
    db.add(session_exercise)
    db.commit()
    db.refresh(session_exercise)
    return session_exercise


@router.get("", response_model=list[schemas.SessionExerciseRead])
def list_session_exercises(
    session_id: int | None = None,
    exercise_id: int | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.SessionExercise)
    if session_id is not None:
        stmt = stmt.where(models.SessionExercise.session_id == session_id)
    if exercise_id is not None:
        stmt = stmt.where(models.SessionExercise.exercise_id == exercise_id)
    stmt = stmt.order_by(models.SessionExercise.order_index)
    return db.scalars(stmt).all()


@router.get("/{session_exercise_id}", response_model=schemas.SessionExerciseRead)
def get_session_exercise(session_exercise_id: int, db: Session = Depends(get_db)):
    session_exercise = db.get(models.SessionExercise, session_exercise_id)
    if session_exercise is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    return session_exercise


@router.patch("/{session_exercise_id}", response_model=schemas.SessionExerciseRead)
def update_session_exercise(
    session_exercise_id: int,
    payload: schemas.SessionExerciseUpdate,
    db: Session = Depends(get_db),
):
    session_exercise = db.get(models.SessionExercise, session_exercise_id)
    if session_exercise is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session_exercise, field, value)
    db.commit()
    db.refresh(session_exercise)
    return session_exercise


@router.delete("/{session_exercise_id}", status_code=204)
def delete_session_exercise(session_exercise_id: int, db: Session = Depends(get_db)):
    session_exercise = db.get(models.SessionExercise, session_exercise_id)
    if session_exercise is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    db.delete(session_exercise)  # cascades to exercise_sets
    db.commit()
