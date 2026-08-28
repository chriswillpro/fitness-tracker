from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/workout-sessions", tags=["workout sessions"])


@router.post("", response_model=schemas.WorkoutSessionRead, status_code=201)
def create_session(payload: schemas.WorkoutSessionCreate, db: Session = Depends(get_db)):
    if db.get(models.User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    session = models.WorkoutSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[schemas.WorkoutSessionRead])
def list_sessions(
    user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.WorkoutSession)
    if user_id is not None:
        stmt = stmt.where(models.WorkoutSession.user_id == user_id)
    if date_from is not None:
        stmt = stmt.where(models.WorkoutSession.session_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(models.WorkoutSession.session_date <= date_to)
    stmt = stmt.order_by(models.WorkoutSession.session_date.desc())
    return db.scalars(stmt).all()


@router.get("/{session_id}", response_model=schemas.WorkoutSessionRead)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.get(models.WorkoutSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Workout session not found")
    return session


@router.patch("/{session_id}", response_model=schemas.WorkoutSessionRead)
def update_session(
    session_id: int, payload: schemas.WorkoutSessionUpdate, db: Session = Depends(get_db)
):
    session = db.get(models.WorkoutSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Workout session not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.get(models.WorkoutSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Workout session not found")
    db.delete(session)  # cascades to session_exercises -> exercise_sets
    db.commit()
