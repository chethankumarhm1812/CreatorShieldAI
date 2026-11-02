# Architecture

## Logical components

### Creator Portal
Customer-facing experience for onboarding, quote, policy, billing, FNOL and claim tracking.

### Insurer Operations Portal
Underwriter/adjuster experience for policy search, claim investigation, rule evaluation, AI findings, approval and payment.

### PolicyCenter Simulator
Owns the policy domain: creator account, product, quote, underwriting, policy term, coverages, limits and lifecycle.

### ClaimCenter Simulator
Owns incident/FNOL, claim, exposures, evidence, investigation, assessment, adjudication and payment workflow.

### BillingCenter Simulator
Owns billing account, invoice, due dates, payment status and outstanding amount.

### Rules Engine
Pure deterministic Python functions. Rules are testable independently from AI.

### AI Orchestrator
LangGraph state graph. Agents provide structured recommendations only.

## Data ownership principle

- Policy data is owned by the policy domain.
- Claim data is owned by the claim domain.
- Billing data is owned by the billing domain.
- AI assessments are append-only assessment records linked to claims.
- Audit records record actor, role, action, entity and details.

## Security principle

No creator password, session cookie, platform token or authentication secret is requested as claim evidence. Evidence is treated as untrusted input.
