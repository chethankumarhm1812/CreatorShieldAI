from datetime import date, datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from ..database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(40), nullable=False, default="CREATOR")
    full_name = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    creator = relationship("Creator", back_populates="user", uselist=False)

class Creator(Base):
    __tablename__ = "creators"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    business_name = Column(String(160), nullable=False)
    creator_type = Column(String(80), default="Video Creator")
    monthly_revenue = Column(Float, default=200000)
    mfa_enabled = Column(Boolean, default=True)
    recovery_email = Column(Boolean, default=True)
    backup_auth = Column(Boolean, default=True)
    user = relationship("User", back_populates="creator")
    accounts = relationship("CreatorAccount", back_populates="creator")
    policies = relationship("Policy", back_populates="creator")

class CreatorAccount(Base):
    __tablename__ = "creator_accounts"
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("creators.id"))
    platform = Column(String(60), nullable=False)
    handle = Column(String(120), nullable=False)
    monetized = Column(Boolean, default=True)
    security_score = Column(Integer, default=85)
    creator = relationship("Creator", back_populates="accounts")

class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True)
    policy_number = Column(String(40), unique=True, nullable=False)
    creator_id = Column(Integer, ForeignKey("creators.id"))
    product_name = Column(String(160), default="Creator Cyber Interruption & Account Recovery")
    status = Column(String(40), default="ACTIVE")
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    premium = Column(Float, default=7200)
    aggregate_limit = Column(Float, default=150000)
    deductible = Column(Float, default=5000)
    waiting_days = Column(Integer, default=1)
    creator = relationship("Creator", back_populates="policies")
    coverages = relationship("PolicyCoverage", back_populates="policy", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="policy")
    billing = relationship("BillingAccount", back_populates="policy", uselist=False)

class PolicyCoverage(Base):
    __tablename__ = "policy_coverages"
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id"))
    code = Column(String(50), nullable=False)
    name = Column(String(120), nullable=False)
    limit_amount = Column(Float, nullable=False)
    daily_benefit = Column(Float, default=0)
    policy = relationship("Policy", back_populates="coverages")

class BillingAccount(Base):
    __tablename__ = "billing_accounts"
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), unique=True)
    account_number = Column(String(50), unique=True)
    billing_status = Column(String(40), default="CURRENT")
    next_due = Column(Date)
    outstanding = Column(Float, default=0)
    policy = relationship("Policy", back_populates="billing")
    invoices = relationship("Invoice", back_populates="billing_account", cascade="all, delete-orphan")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    billing_account_id = Column(Integer, ForeignKey("billing_accounts.id"))
    invoice_number = Column(String(50), unique=True)
    amount = Column(Float, nullable=False)
    due_date = Column(Date)
    status = Column(String(30), default="DUE")
    billing_account = relationship("BillingAccount", back_populates="invoices")
    payments = relationship("BillingPayment", back_populates="invoice", cascade="all, delete-orphan")

class BillingPayment(Base):
    __tablename__ = "billing_payments"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    amount = Column(Float, nullable=False)
    status = Column(String(30), default="PAID")
    reference = Column(String(80), unique=True)
    processed_at = Column(DateTime(timezone=True), default=utc_now)
    invoice = relationship("Invoice", back_populates="payments")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("creators.id"))
    incident_number = Column(String(50), unique=True)
    incident_type = Column(String(80), nullable=False)
    platform = Column(String(60), nullable=False)
    occurred_on = Column(Date, nullable=False)
    restored_on = Column(Date)
    description = Column(Text, nullable=False)
    exclusion_code = Column(String(80))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    claims = relationship("Claim", back_populates="incident")

class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True)
    claim_number = Column(String(50), unique=True)
    policy_id = Column(Integer, ForeignKey("policies.id"))
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    status = Column(String(40), default="FNOL")
    claimed_amount = Column(Float, default=0)
    eligible_amount = Column(Float, default=0)
    recommended_payout = Column(Float, default=0)
    risk_level = Column(String(30), default="LOW")
    decision_reason = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    policy = relationship("Policy", back_populates="claims")
    incident = relationship("Incident", back_populates="claims")
    evidences = relationship("Evidence", back_populates="claim", cascade="all, delete-orphan")
    exposures = relationship("ClaimExposure", back_populates="claim", cascade="all, delete-orphan")
    assessments = relationship("AgentAssessment", back_populates="claim", cascade="all, delete-orphan")
    decisions = relationship("ClaimDecision", back_populates="claim", cascade="all, delete-orphan")
    payment = relationship("ClaimPayment", back_populates="claim", uselist=False, cascade="all, delete-orphan")

class ClaimExposure(Base):
    __tablename__ = "claim_exposures"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    coverage_code = Column(String(50))
    claimed_amount = Column(Float, default=0)
    eligible_amount = Column(Float, default=0)
    status = Column(String(30), default="OPEN")
    claim = relationship("Claim", back_populates="exposures")

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    evidence_type = Column(String(80))
    file_name = Column(String(255))
    verification_status = Column(String(30), default="PENDING")
    verified_amount = Column(Float, default=0)
    notes = Column(Text, default="")
    claim = relationship("Claim", back_populates="evidences")

class AgentAssessment(Base):
    __tablename__ = "agent_assessments"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    agent_name = Column(String(80))
    findings = Column(Text)
    confidence = Column(Float, default=0)
    recommendation = Column(String(80))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    claim = relationship("Claim", back_populates="assessments")

class ClaimDecision(Base):
    __tablename__ = "claim_decisions"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    actor_role = Column(String(40))
    decision = Column(String(40))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    claim = relationship("Claim", back_populates="decisions")

class ClaimPayment(Base):
    __tablename__ = "claim_payments"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), unique=True)
    amount = Column(Float)
    status = Column(String(30), default="PENDING")
    reference = Column(String(80))
    processed_at = Column(DateTime(timezone=True))
    claim = relationship("Claim", back_populates="payment")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    actor = Column(String(120))
    role = Column(String(40))
    action = Column(String(120))
    entity_type = Column(String(60))
    entity_id = Column(String(80))
    details = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utc_now)
