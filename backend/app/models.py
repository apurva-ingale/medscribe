import datetime as dt
import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="doctor")


class Consultation(Base):
    __tablename__ = "consultations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    patient_label: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded|processing|review|finalized|failed
    stage: Mapped[str] = mapped_column(String(30), default="")
    audio_path: Mapped[str] = mapped_column(String(500))
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    flags: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finalized_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    doctor: Mapped[User] = relationship(lazy="joined")
