from datetime import date, timedelta
from sqlalchemy.orm import Session
from ..models.models import *
from ..rules.policy_rules import evaluate_policy, calculate_loss
from ..agents.graph import run_claim_agents


def audit(db, user, action, entity_type, entity_id, details=""):
    db.add(AuditEvent(actor=user.email if user else "SYSTEM", role=user.role if user else "SYSTEM", action=action, entity_type=entity_type, entity_id=str(entity_id), details=details))

def upgrade_demo_seed(db):
    claim=db.query(Claim).filter_by(claim_number="CLM-CS-1001",decision_reason="Synthetic demonstration claim").first()
    if not claim or claim.status!="PENDING_APPROVAL" or not claim.payment or claim.payment.status!="PENDING":
        return
    claim.eligible_amount=60000
    claim.recommended_payout=55000
    for exposure in claim.exposures:
        if exposure.coverage_code=="INTERRUPTION":
            exposure.eligible_amount=20000
    evidence_amounts={
        "recovery-invoice.pdf":30000,
        "legal-counsel-invoice.pdf":10000,
        "revenue-statement.csv":25000,
    }
    existing_files={item.file_name for item in claim.evidences}
    for evidence in claim.evidences:
        if evidence.file_name in evidence_amounts and not evidence.verified_amount:
            evidence.verified_amount=evidence_amounts[evidence.file_name]
    if "legal-counsel-invoice.pdf" not in existing_files:
        db.add(Evidence(claim_id=claim.id,evidence_type="Legal Counsel Invoice",file_name="legal-counsel-invoice.pdf",verification_status="VERIFIED",verified_amount=10000,notes="Eligible legal expense."))
    claim.payment.amount=55000
    claim.decision_reason="Synthetic demonstration claim; adjuster review is pending."
    db.commit()

def seed(db):
    if db.query(User).count():
        upgrade_demo_seed(db)
        return
    creator_user = User(email="creator@example.com", password_hash="", role="CREATOR", full_name="Aarav Creator")
    adjuster = User(email="adjuster@example.com", password_hash="", role="ADJUSTER", full_name="Maya Adjuster")
    from ..security import hash_password
    creator_user.password_hash = hash_password("Creator@123"); adjuster.password_hash = hash_password("Adjuster@123")
    db.add_all([creator_user, adjuster]); db.flush()
    creator = Creator(user_id=creator_user.id, business_name="Aarav Media Studio", monthly_revenue=200000)
    db.add(creator); db.flush()
    db.add(CreatorAccount(creator_id=creator.id, platform="YouTube", handle="@aaravstudio", monetized=True, security_score=87))
    p = Policy(policy_number="CS-2026-0001", creator_id=creator.id, effective_date=date(2026,1,1), expiry_date=date(2027,1,1), premium=7200, aggregate_limit=150000, deductible=5000, waiting_days=1)
    db.add(p); db.flush()
    db.add_all([
        PolicyCoverage(policy_id=p.id, code="RECOVERY", name="Account Recovery Expenses", limit_amount=50000),
        PolicyCoverage(policy_id=p.id, code="INTERRUPTION", name="Revenue Interruption", limit_amount=75000, daily_benefit=5000),
        PolicyCoverage(policy_id=p.id, code="LEGAL", name="Cyber Legal Assistance", limit_amount=50000),
        PolicyCoverage(policy_id=p.id, code="RESTORATION", name="Creator Business Restoration", limit_amount=25000),
    ])
    b = BillingAccount(policy_id=p.id, account_number="BA-CS-0001", billing_status="CURRENT", next_due=date(2026,11,1), outstanding=0)
    db.add(b); db.flush(); db.add(Invoice(billing_account_id=b.id, invoice_number="INV-CS-1001", amount=7200, due_date=date(2026,1,15), status="PAID"))
    inc = Incident(creator_id=creator.id, incident_number="INC-CS-1001", incident_type="ACCOUNT_TAKEOVER", platform="YouTube", occurred_on=date(2026,10,18), restored_on=date(2026,10,23), description="Unauthorized access caused a five-day creator account interruption.")
    db.add(inc); db.flush()
    claim = Claim(claim_number="CLM-CS-1001", policy_id=p.id, incident_id=inc.id, status="PENDING_APPROVAL", claimed_amount=65000, eligible_amount=60000, recommended_payout=55000, risk_level="LOW", decision_reason="Synthetic demonstration claim; adjuster review is pending.")
    db.add(claim); db.flush()
    db.add_all([Evidence(claim_id=claim.id, evidence_type="Platform Security Alert", file_name="youtube-security-alert.pdf", verification_status="VERIFIED", notes="Account takeover timestamp matches incident."), Evidence(claim_id=claim.id, evidence_type="Recovery Invoice", file_name="recovery-invoice.pdf", verification_status="VERIFIED", verified_amount=30000, notes="₹30,000 recovery expense."), Evidence(claim_id=claim.id, evidence_type="Legal Counsel Invoice", file_name="legal-counsel-invoice.pdf", verification_status="VERIFIED", verified_amount=10000, notes="Eligible legal expense."), Evidence(claim_id=claim.id, evidence_type="Revenue Statement", file_name="revenue-statement.csv", verification_status="VERIFIED", verified_amount=25000, notes="Historical revenue supports interruption assessment.")])
    db.add_all([ClaimExposure(claim_id=claim.id, coverage_code="RECOVERY", claimed_amount=30000, eligible_amount=30000), ClaimExposure(claim_id=claim.id, coverage_code="LEGAL", claimed_amount=10000, eligible_amount=10000), ClaimExposure(claim_id=claim.id, coverage_code="INTERRUPTION", claimed_amount=25000, eligible_amount=20000)])
    db.add_all([AgentAssessment(claim_id=claim.id, agent_name="Incident Triage Agent", findings="Account takeover classified as high-severity covered incident.", confidence=.94, recommendation="PROCEED"), AgentAssessment(claim_id=claim.id, agent_name="Evidence Investigation Agent", findings="Four evidence items are adjuster-verified; incident timeline is consistent.", confidence=.91, recommendation="PROCEED"), AgentAssessment(claim_id=claim.id, agent_name="Risk Review Agent", findings="No duplicate evidence detected in demo data.", confidence=.88, recommendation="LOW_RISK"), AgentAssessment(claim_id=claim.id, agent_name="Loss Assessment Agent", findings="₹60,000 eligible after the one-day waiting period; ₹5,000 deductible applies.", confidence=.97, recommendation="₹55,000")])
    db.add(ClaimPayment(claim_id=claim.id, amount=55000, status="PENDING", reference="PAY-CS-1001"))
    db.commit()
