from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    business_name: str = Field(min_length=2, max_length=160)
    creator_type: str = Field(default="Digital Creator", min_length=2, max_length=80)
    platform: str = Field(min_length=2, max_length=60)
    handle: str = Field(min_length=2, max_length=120)
    mfa_enabled: bool = False
    recovery_email: bool = False
    backup_auth: bool = False

class IncidentCreate(BaseModel):
    incident_type: Literal["ACCOUNT_TAKEOVER", "MALWARE_COMPROMISE", "RANSOMWARE", "COVERED_RESTRICTION"]
    platform: str = Field(min_length=2, max_length=60)
    occurred_on: date
    restored_on: date | None = None
    description: str = Field(min_length=10, max_length=3000)

    @model_validator(mode="after")
    def validate_incident_dates(self):
        if self.occurred_on > date.today():
            raise ValueError("Incident date cannot be in the future")
        if self.restored_on and self.restored_on < self.occurred_on:
            raise ValueError("Restoration date cannot be before the incident date")
        return self

class ClaimIntake(BaseModel):
    recovery_expense: float = Field(default=0, ge=0, le=500000)
    legal_expense: float = Field(default=0, ge=0, le=500000)
    revenue_loss: float = Field(default=0, ge=0, le=500000)

class FNOLCreate(IncidentCreate):
    recovery_expense: float = Field(default=0, ge=0, le=500000)
    legal_expense: float = Field(default=0, ge=0, le=500000)
    revenue_loss: float = Field(default=0, ge=0, le=500000)

class EvidenceCreate(BaseModel):
    evidence_type: str = Field(min_length=2, max_length=80)
    file_name: str = Field(min_length=1, max_length=255)
    notes: str = ""

class EvidenceVerification(BaseModel):
    verified: bool
    reason: str = Field(min_length=5, max_length=2000)
    verified_amount: float | None = Field(default=None, ge=0, le=500000)

class ExclusionUpdate(BaseModel):
    code: Literal[
        "INTENTIONAL_SELF_INFLICTED",
        "FRAUDULENT_CLAIM",
        "UNSUPPORTED_LOSS",
        "NON_COVERED_PLATFORM_VIOLATION",
        "PRE_EXISTING_INCIDENT",
    ] | None
    reason: str = Field(min_length=5, max_length=2000)

class DecisionCreate(BaseModel):
    decision: str = Field(min_length=1, max_length=40)
    reason: str = Field(min_length=5, max_length=2000)

class QuoteRequest(BaseModel):
    requested_limit: float = Field(gt=0)
    platform: str = Field(min_length=2, max_length=60)
    security_score: int = Field(default=0, ge=0, le=100)

class AccountCreate(BaseModel):
    platform: str = Field(min_length=2, max_length=60)
    handle: str = Field(min_length=2, max_length=120)
    monetized: bool = True
