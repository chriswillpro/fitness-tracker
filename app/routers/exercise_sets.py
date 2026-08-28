from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/exercise-sets", tags=["exercise sets"])


@router.post("", response_model=schemas.ExerciseSetRead, status_code=201)
def create_exercise_set(payload: schemas.ExerciseSetCreate, db: Session = Depends(get_db)):
    if db.get(models.SessionExercise, payload.session_exercise_id) is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    exercise_set = models.ExerciseSet(**payload.model_dump())
    db.add(exercise_set)
    db.commit()
    db.refresh(exercise_set)
    return exercise_set


@router.get("", response_model=list[schemas.ExerciseSetRead])
def list_exercise_sets(
    session_exercise_id: int | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.ExerciseSet)
    if session_exercise_id is not None:
        stmt = stmt.where(models.ExerciseSet.session_exercise_id == session_exercise_id)
    stmt = stmt.order_by(models.ExerciseSet.set_number)
    return db.scalars(stmt).all()


@router.get("/{set_id}", response_model=schemas.ExerciseSetRead)
def get_exercise_set(set_id: int, db: Session = Depends(get_db)):
    exercise_set = db.get(models.ExerciseSet, set_id)
    if exercise_set is None:
        raise HTTPException(status_code=404, detail="Exercise set not found")
    return exercise_set


@router.patch("/{set_id}", response_model=schemas.ExerciseSetRead)
def update_exercise_set(
    set_id: int, payload: schemas.ExerciseSetUpdate, db: Session = Depends(get_db)
):
    exercise_set = db.get(models.ExerciseSet, set_id)
    if exercise_set is None:
        raise HTTPException(status_code=404, detail="Exercise set not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exercise_set, field, value)
    db.commit()
    db.refresh(exercise_set)
    return exercise_set


@router.delete("/{set_id}", status_code=204)
def delete_exercise_set(set_id: int, db: Session = Depends(get_db)):
    exercise_set = db.get(models.ExerciseSet, set_id)
    if exercise_set is None:
        raise HTTPException(status_code=404, detail="Exercise set not found")
    db.delete(exercise_set)
    db.commit()
