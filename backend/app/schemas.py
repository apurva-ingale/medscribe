from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SECTIONS = [
    "chief_complaint", "history_of_present_illness", "symptoms", "past_medical_history",
    "medications", "allergies", "examination_findings", "assessment", "plan", "follow_up",
]


class Item(BaseModel):
    text: str = Field(description="One concise clinical statement, only facts stated in the consultation")
    source_quote: str = Field(description="Short verbatim excerpt of the transcript that supports this statement")


class ClinicalNote(BaseModel):
    chief_complaint: list[Item]
    history_of_present_illness: list[Item]
    symptoms: list[Item]
    past_medical_history: list[Item]
    medications: list[Item]
    allergies: list[Item]
    examination_findings: list[Item]
    assessment: list[Item]
    plan: list[Item]
    follow_up: list[Item]


class Flag(BaseModel):
    section: str
    index: int  # -1 = whole section
    reason: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: str


class UserCreate(BaseModel):
    email: str
    name: str
    password: str = Field(min_length=8)
    role: Literal["doctor", "admin"] = "doctor"


class ConsultationOut(BaseModel):
    id: str
    patient_label: str
    status: str
    stage: str
    transcript: str | None
    note: ClinicalNote | None
    flags: list[Flag]
    error: str | None
    created_at: datetime
    finalized_at: datetime | None
    doctor_name: str


class FinalizeIn(BaseModel):
    confirm_flags: bool = False
