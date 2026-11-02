# API reference

FastAPI serves the versioned-by-prefix demo API under `/api`; interactive OpenAPI documentation is available at `/docs`.

## Authentication

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/auth/register` | Public; creates a creator profile and first account |
| POST | `/api/auth/login` | Public |
| GET | `/api/me` | Authenticated |

Authenticated endpoints use `Authorization: Bearer <JWT>`. Adjuster routes enforce role checks. Creator access to claims, policies, billing and audit data is scoped to that creator.

## Accounts and policy

| Method | Endpoint | Access |
|---|---|---|
| GET / POST | `/api/accounts` | Authenticated / Creator |
| GET | `/api/dashboard` | Authenticated |
| GET | `/api/policies` | Authenticated; creators see their own policies |
| GET | `/api/policies/{policy_id}` | Authenticated; ownership checked |
| POST | `/api/quotes` | Creator |
| POST | `/api/policies/bind` | Creator; standard underwriting only |

## Billing

| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/billing` | Authenticated; creators see their own billing accounts |
| POST | `/api/billing/invoices/{invoice_id}/pay` | Invoice owner; simulated payment |

Paying an initial invoice activates the corresponding bound policy and updates the billing account balance.

## Claims

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/incidents` | Creator |
| POST | `/api/claims/fnol` | Creator; atomically creates the incident, claim and requested exposures |
| POST | `/api/claims/from-incident/{incident_id}` | Creator; requires active policy and claimed exposure amounts |
| GET | `/api/claims` | Authenticated; creator-scoped |
| GET | `/api/claims/{claim_id}` | Authenticated; ownership checked |
| POST | `/api/claims/{claim_id}/evidence` | Creator or adjuster; evidence remains pending |
| POST | `/api/claims/{claim_id}/evidence/{evidence_id}/verify` | Adjuster; records verification reason and supported amount |
| POST | `/api/claims/{claim_id}/exclusion` | Adjuster; records or clears a configured exclusion flag |
| POST | `/api/claims/{claim_id}/investigate` | Adjuster |
| POST | `/api/claims/{claim_id}/assess` | Adjuster; deterministic rules and loss calculation |
| POST | `/api/claims/{claim_id}/decision` | Adjuster; `APPROVE`, `DENY`, or `REQUEST_INFORMATION`, with reason |
| POST | `/api/claims/{claim_id}/pay` | Adjuster; approved claims only |
| POST | `/api/claims/{claim_id}/close` | Adjuster; paid or denied claims only |

## Audit

`GET /api/audit/{entity_type}/{entity_id}` returns ordered audit events. Creator ownership is checked for claim and policy entities.

## Sample claim intake

```json
{
  "recovery_expense": 30000,
  "legal_expense": 10000,
  "revenue_loss": 25000
}
```

Creator-entered amounts are claims, not approved losses. Financial evidence must be verified by an adjuster; eligible revenue interruption is also capped by the configured daily benefit, waiting period and policy limits.
