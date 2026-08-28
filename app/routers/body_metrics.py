from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/body-metrics", tags=["body metrics"])


@router.post("", response_model=schemas.BodyMetricRead, status_code=201)
def create_body_metric(payload: schemas.BodyMetricCreate, db: Session = Depends(get_db)):
    if db.get(models.User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    metric = models.BodyMetric(**payload.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("", response_model=list[schemas.BodyMetricRead])
def list_body_metrics(
    user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.BodyMetric)
    if user_id is not None:
        stmt = stmt.where(models.BodyMetric.user_id == user_id)
    if date_from is not None:
        stmt = stmt.where(models.BodyMetric.metric_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(models.BodyMetric.metric_date <= date_to)
    stmt = stmt.order_by(models.BodyMetric.metric_date.desc())
    return db.scalars(stmt).all()


@router.get("/{metric_id}", response_model=schemas.BodyMetricRead)
def get_body_metric(metric_id: int, db: Session = Depends(get_db)):
    metric = db.get(models.BodyMetric, metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="Body metric not found")
    return metric


@router.patch("/{metric_id}", response_model=schemas.BodyMetricRead)
def update_body_metric(
    metric_id: int, payload: schemas.BodyMetricUpdate, db: Session = Depends(get_db)
):
    metric = db.get(models.BodyMetric, metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="Body metric not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(metric, field, value)
    db.commit()
    db.refresh(metric)
    return metric


@router.delete("/{metric_id}", status_code=204)
def delete_body_metric(metric_id: int, db: Session = Depends(get_db)):
    metric = db.get(models.BodyMetric, metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="Body metric not found")
    db.delete(metric)
    db.commit()
