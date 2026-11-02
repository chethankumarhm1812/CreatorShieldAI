from datetime import date
from dataclasses import dataclass

@dataclass
class RuleResult:
    code: str
    passed: bool
    message: str
    severity: str = "INFO"

COVERED_INCIDENTS = {"ACCOUNT_TAKEOVER", "MALWARE_COMPROMISE", "RANSOMWARE", "COVERED_RESTRICTION"}

CLAIM_TRANSITIONS = {
    "FNOL": {"OPEN"},
    "OPEN": {"INITIAL_REVIEW", "INVESTIGATION", "EVIDENCE_REQUIRED"},
    "INITIAL_REVIEW": {"INVESTIGATION", "EVIDENCE_REQUIRED", "COVERAGE_REVIEW"},
    "INVESTIGATION": {"EVIDENCE_REQUIRED", "COVERAGE_REVIEW"},
    "EVIDENCE_REQUIRED": {"INVESTIGATION", "COVERAGE_REVIEW"},
    "COVERAGE_REVIEW": {"EVIDENCE_REQUIRED", "LOSS_ASSESSMENT", "PENDING_APPROVAL", "DENIED"},
    "LOSS_ASSESSMENT": {"EVIDENCE_REQUIRED", "PENDING_APPROVAL"},
    "PENDING_APPROVAL": {"APPROVED", "DENIED", "EVIDENCE_REQUIRED", "COVERAGE_REVIEW"},
    "APPROVED": {"PAYMENT_PENDING"},
    "PAYMENT_PENDING": {"PAID"},
    "PAID": {"CLOSED"},
    "DENIED": {"CLOSED"},
    "CLOSED": set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in CLAIM_TRANSITIONS.get(current, set())


def evaluate_policy(policy, incident, creator, evidence_count: int):
    results = []
    active = policy.effective_date <= incident.occurred_on <= policy.expiry_date and policy.status == "ACTIVE"
    results.append(RuleResult("POLICY_PERIOD", active, "Incident falls within the active policy period." if active else "Incident is outside the active policy period.", "BLOCK" if not active else "INFO"))
    covered = incident.incident_type in COVERED_INCIDENTS
    results.append(RuleResult("COVERED_EVENT", covered, "Incident type is covered." if covered else "Incident type is not covered.", "BLOCK" if not covered else "INFO"))
    security_ok = creator.mfa_enabled and creator.recovery_email and creator.backup_auth
    results.append(RuleResult("SECURITY_CONTROLS", security_ok, "Required account security controls are present." if security_ok else "Required security controls are incomplete.", "WARN" if not security_ok else "INFO"))
    evidence_ok = evidence_count >= 2
    results.append(RuleResult("MIN_EVIDENCE", evidence_ok, "Minimum evidence threshold met." if evidence_ok else "At least two evidence items are required before final adjudication.", "REVIEW" if not evidence_ok else "INFO"))
    exclusion = getattr(incident, "exclusion_code", None)
    results.append(RuleResult("EXCLUSION_SCREEN", not bool(exclusion), "No configured exclusion was identified." if not exclusion else f"Configured exclusion applies: {exclusion}.", "BLOCK" if exclusion else "INFO"))
    return results


def calculate_loss(policy, incident, exposures):
    details = []
    total = 0.0
    remaining_aggregate = max(0.0, float(policy.aggregate_limit))
    for item in exposures:
        claimed = max(0.0, float(item.get("claimed", 0)))
        cap = max(0.0, float(item.get("limit", 0)))
        eligible = min(claimed, cap)
        covered_days = None
        waiting_days = 0
        if item.get("coverage") == "INTERRUPTION":
            waiting_days = max(0, int(item.get("waiting_days", policy.waiting_days)))
            elapsed_days = max(0, int(item.get("days", 0)))
            covered_days = max(0, elapsed_days - waiting_days)
            daily_benefit = max(0.0, float(item.get("daily_benefit", 0)))
            eligible = min(eligible, covered_days * daily_benefit)
        if not item.get("verified", True):
            eligible = 0.0
        if item.get("verified_amount") is not None:
            eligible = min(eligible, max(0.0, float(item["verified_amount"])))
        eligible = min(eligible, remaining_aggregate)
        details.append({
            "coverage": item["coverage"],
            "claimed": claimed,
            "eligible": eligible,
            "cap": cap,
            "covered_days": covered_days,
            "waiting_days_applied": waiting_days,
            "evidence_verified": bool(item.get("verified", True)),
        })
        total += eligible
        remaining_aggregate -= eligible
    deductible = min(policy.deductible, total)
    payout = max(0.0, total - deductible)
    return {"gross_eligible": total, "deductible": deductible, "payout": payout, "details": details}
