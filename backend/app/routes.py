import datetime as dt
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import current_user, hash_pw, make_token, require_admin, verify_pw
from .config import settings
from .db import get_db
from .models import Consultation, User
from .pipeline import run_pipeline
from .schemas import ClinicalNote, ConsultationOut, FinalizeIn, Flag, UserCreate, UserOut
from .validation import validate_note

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
router = APIRouter(prefix="/api/consultations", tags=["consultations"])


@auth_router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    if not user or not verify_pw(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": make_token(user), "token_type": "bearer"}


@auth_router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@auth_router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@auth_router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "A user with this email already exists")
    user = User(email=email, name=body.name.strip(), password_hash=hash_pw(body.password), role=body.role)
    db.add(user)
    db.commit()
    return user


def to_out(c: Consultation) -> ConsultationOut:
    return ConsultationOut(
        id=c.id, patient_label=c.patient_label, status=c.status, stage=c.stage, transcript=c.transcript,
        note=ClinicalNote.model_validate(c.note) if c.note else None,
        flags=[Flag(**f) for f in (c.flags or [])], error=c.error,
        created_at=c.created_at, finalized_at=c.finalized_at, doctor_name=c.doctor.name,
    )


def _get(db: Session, cid: str, user: User) -> Consultation:
    c = db.get(Consultation, cid)
    if not c or (user.role != "admin" and c.doctor_id != user.id):
        raise HTTPException(404, "Consultation not found")
    return c


@router.post("", response_model=ConsultationOut, status_code=201)
def create(
    background: BackgroundTasks,
    patient_label: str = Form(..., min_length=1, max_length=200),
    audio: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    cid = str(uuid.uuid4())
    path = Path(settings.upload_dir) / f"{cid}{Path(audio.filename or '').suffix or '.webm'}"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        shutil.copyfileobj(audio.file, f)
    c = Consultation(id=cid, doctor_id=user.id, patient_label=patient_label.strip(), audio_path=str(path))
    db.add(c)
    db.commit()
    db.refresh(c)
    background.add_task(run_pipeline, cid)
    return to_out(c)


@router.get("", response_model=list[ConsultationOut])
def list_consultations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Consultation).order_by(Consultation.created_at.desc())
    if user.role != "admin":
        q = q.where(Consultation.doctor_id == user.id)
    return [to_out(c) for c in db.scalars(q).unique().all()]


@router.get("/{cid}", response_model=ConsultationOut)
def get_one(cid: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return to_out(_get(db, cid, user))


@router.put("/{cid}/note", response_model=ConsultationOut)
def update_note(cid: str, note: ClinicalNote, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = _get(db, cid, user)
    if c.status != "review":
        raise HTTPException(409, "Only notes under review can be edited")
    c.note = note.model_dump()
    c.flags = [f.model_dump() for f in validate_note(note, c.transcript or "")]
    db.commit()
    return to_out(c)


@router.post("/{cid}/finalize", response_model=ConsultationOut)
def finalize(cid: str, body: FinalizeIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = _get(db, cid, user)
    if c.status != "review":
        raise HTTPException(409, "Only notes under review can be finalized")
    if c.flags and not body.confirm_flags:
        raise HTTPException(409, f"{len(c.flags)} flagged item(s) need review; confirm to finalize anyway")
    c.status, c.finalized_at = "finalized", dt.datetime.now(dt.timezone.utc)
    db.commit()
    return to_out(c)
