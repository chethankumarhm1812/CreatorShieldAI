# Business rules and adjudication

Coverage and payable amounts are evaluated by Python rules, not by the AI graph. A human adjuster owns the final approval, denial or information request.

## Policy eligibility and coverage

1. A creator must have an active policy for a claim FNOL. `BOUND` is not active; the first invoice must be paid.
2. Incident date must satisfy `effective_date <= occurred_on <= expiry_date`, and policy status must be `ACTIVE`.
3. Covered incident types are `ACCOUNT_TAKEOVER`, `MALWARE_COMPROMISE`, `RANSOMWARE` and `COVERED_RESTRICTION`.
4. MFA, recovery email and backup authentication are evaluated as security controls. Missing controls are a warning/referral signal, not an AI decision.
5. Evidence references remain pending until an adjuster verifies them. Each financial exposure requires a matching verified document and a verified monetary amount.

## Loss calculation

For each exposure:

- Eligible recovery/legal loss is no greater than the lowest of the claimed amount, supported verified amount and coverage sublimit.
- Revenue interruption is no greater than the lowest of claimed loss, supported verified revenue loss, coverage sublimit and `eligible_days × daily_benefit`.
- `eligible_days = max(0, elapsed_interruption_days - waiting_days)`.
- Exposure eligibility is applied in sequence and capped by the remaining aggregate policy limit.
- One policy deductible is subtracted from total eligible loss; payout cannot be negative.

The adjuster view displays claimed, eligible and payable/recommended amounts separately. Financial proof must be verified; creator-entered amounts alone never establish eligibility. Adjusters can record a configured exclusion code; such flags block payment pending human adjudication.

## Human review and claim state

The state machine is centralized in `backend/app/rules/policy_rules.py`. It rejects invalid or skipped transitions. High risk, missing evidence and blocked coverage remain review outcomes; the engine does not turn an AI recommendation into an automatic claim approval.

An adjuster approval requires `PENDING_APPROVAL`, no blocking policy rules, verified exposure evidence and a positive calculated payout. A reason is required for approval, denial and requests for information. Each evidence review and consequential action is audited.

## Deliberate simulator boundaries

Automatic exclusion discovery, platform-contract interpretation, source-system revenue ingestion, reserves, renewal/endorsement and delinquency-driven cancellation are not full production implementations. The local simulator provides configurable policy values in SQLite and demonstrates the rule boundary without representing a legally binding insurance contract.
