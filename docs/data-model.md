# Data model

SQLAlchemy models persist the demo domain in SQLite. The database URL is configurable for a later PostgreSQL deployment. `create_all` initializes new tables; a small startup migration adds `evidence.verified_amount` to existing SQLite demo databases.

| Entity | Responsibility / key links |
|---|---|
| `User` | Login identity, password hash and `CREATOR` / `ADJUSTER` role |
| `Creator` | Business profile and declared MFA, recovery-email and backup-auth controls |
| `CreatorAccount` | Platform, handle, monetization and derived security score |
| `Policy` | Policy number, term, status, premium, aggregate limit, deductible and waiting days |
| `PolicyCoverage` | Coverage code, per-exposure limit and daily benefit |
| `BillingAccount` | Policy-linked account, due date, status and outstanding balance |
| `Invoice` / `BillingPayment` | Premium invoice and simulated payment reference |
| `Incident` | FNOL type, date, platform, restoration date and narrative |
| `Claim` | Claim number, policy, incident, lifecycle status and calculated amounts |
| `ClaimExposure` | Per-coverage claimed and eligible amounts |
| `Evidence` | Evidence type/reference, verification state, supported amount and notes |
| `AgentAssessment` | Append-only AI findings, confidence and recommendation |
| `ClaimDecision` | Adjuster role, decision, reason and timestamp |
| `ClaimPayment` | Simulated claim settlement status and payment reference |
| `AuditEvent` | Actor, role, action, entity, identifier, details and timestamp |

Evidence is represented by a filename/reference in this demo; document bytes are not stored. The adjuster records a supported amount only after reviewing the referenced evidence. No payment provider is connected.
