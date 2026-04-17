from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SexEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class PatientInput(BaseModel):
    age: int = Field(..., ge=0, le=120)
    sex: SexEnum
    conditions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class MedicationInput(BaseModel):
    name: str = Field(..., min_length=1)
    dosage: Optional[str] = None
    rxcui: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank or whitespace-only")
        return v


class Supplement(BaseModel):
    name: str = Field(..., min_length=1)
    dose: Optional[str] = None
    type: Optional[str] = None  # "herbal" | "ayurvedic" | "homeopathic" | "vitamin" | "other"


class AnalysisRequest(BaseModel):
    patient: PatientInput
    current_medications: list[MedicationInput] = Field(..., min_length=1)
    candidate_medication: MedicationInput
    supplements: list[Supplement] = Field(default_factory=list)
    sedation_requested: bool = False
    sedation_agent_requested: Optional[str] = None
    additional_notes: Optional[str] = None
