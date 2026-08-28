import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/progress-photos", tags=["progress photos"])

# Local-disk storage for now — photo_url is just a TEXT reference in the DB,
# so swapping this for Supabase Storage/Cloudinary later (upload there,
# store the resulting URL instead) needs no schema/model change.
MEDIA_ROOT = Path("media") / "progress_photos"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("", response_model=schemas.ProgressPhotoRead, status_code=201)
def create_progress_photo(
    payload: schemas.ProgressPhotoCreate, db: Session = Depends(get_db)
):
    if db.get(models.User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.body_metric_id is not None and db.get(
        models.BodyMetric, payload.body_metric_id
    ) is None:
        raise HTTPException(status_code=404, detail="Body metric not found")
    data = payload.model_dump(exclude_unset=True)
    photo = models.ProgressPhoto(**data)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.post("/upload", response_model=schemas.ProgressPhotoRead, status_code=201)
def upload_progress_photo(
    user_id: int = Form(...),
    body_metric_id: int | None = Form(None),
    taken_at: datetime | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    if body_metric_id is not None and db.get(models.BodyMetric, body_metric_id) is None:
        raise HTTPException(status_code=404, detail="Body metric not found")
    ext = ALLOWED_CONTENT_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="Unsupported image type (use JPEG, PNG, or WebP)")

    filename = f"{uuid.uuid4().hex}{ext}"
    (MEDIA_ROOT / filename).write_bytes(file.file.read())

    fields = {
        "user_id": user_id,
        "body_metric_id": body_metric_id,
        "photo_url": f"/media/progress_photos/{filename}",
    }
    if taken_at is not None:
        fields["taken_at"] = taken_at
    photo = models.ProgressPhoto(**fields)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.get("", response_model=list[schemas.ProgressPhotoRead])
def list_progress_photos(
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.ProgressPhoto)
    if user_id is not None:
        stmt = stmt.where(models.ProgressPhoto.user_id == user_id)
    stmt = stmt.order_by(models.ProgressPhoto.taken_at.desc())
    return db.scalars(stmt).all()


@router.get("/{photo_id}", response_model=schemas.ProgressPhotoRead)
def get_progress_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(models.ProgressPhoto, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Progress photo not found")
    return photo


@router.patch("/{photo_id}", response_model=schemas.ProgressPhotoRead)
def update_progress_photo(
    photo_id: int, payload: schemas.ProgressPhotoUpdate, db: Session = Depends(get_db)
):
    photo = db.get(models.ProgressPhoto, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Progress photo not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(photo, field, value)
    db.commit()
    db.refresh(photo)
    return photo


@router.delete("/{photo_id}", status_code=204)
def delete_progress_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(models.ProgressPhoto, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Progress photo not found")
    if photo.photo_url.startswith("/media/progress_photos/"):
        (Path("media") / "progress_photos" / Path(photo.photo_url).name).unlink(missing_ok=True)
    db.delete(photo)
    db.commit()
