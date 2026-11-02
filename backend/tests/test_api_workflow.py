import os
import shutil
import tempfile
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    database_dir = Path(tempfile.mkdtemp(prefix="creatorshield-api-test-"))
    database_file = (database_dir / "workflow.db").as_posix()
    os.environ["DATABASE_URL"] = f"sqlite:///{database_file}"
    os.environ["SECRET_KEY"] = "test-only-secret-for-isolated-api-workflow"
    from app.main import app
    from app.database import engine

    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()
    shutil.rmtree(database_dir)


def test_complete_policy_and_claim_workflow(client):
    assert client.get("/api/dashboard").status_code in {401, 403}
    registration = client.post("/api/auth/register", json={
        "email": "workflow.creator@example.test",
        "password": "StrongDemoPass123",
        "full_name": "Workflow Creator",
        "business_name": "Workflow Studio",
        "creator_type": "Video Creator",
        "platform": "YouTube",
        "handle": "@workflow",
        "mfa_enabled": True,
        "recovery_email": True,
        "backup_auth": True,
    })
    assert registration.status_code == 200, registration.text
    creator_headers = {"Authorization": f"Bearer {registration.json()['token']}"}
    assert client.post("/api/auth/register", json={
        "email": "workflow.creator@example.test", "password": "StrongDemoPass123",
        "full_name": "Duplicate", "business_name": "Duplicate Studio",
        "platform": "YouTube", "handle": "@duplicate",
    }).status_code == 409

    quote = client.post("/api/quotes", headers=creator_headers, json={
        "requested_limit": 150000, "platform": "YouTube",
    })
    assert quote.status_code == 200 and quote.json()["underwriting"] == "STANDARD"
    bound = client.post("/api/policies/bind", headers=creator_headers, json={
        "requested_limit": 150000, "platform": "YouTube",
    })
    assert bound.status_code == 200, bound.text
    invoice_id = bound.json()["invoice_id"]
    premium = client.post(f"/api/billing/invoices/{invoice_id}/pay", headers=creator_headers)
    assert premium.status_code == 200 and premium.json()["policy_status"] == "ACTIVE"
    assert client.post(f"/api/billing/invoices/{invoice_id}/pay", headers=creator_headers).status_code == 409

    created_claim = client.post("/api/claims/fnol", headers=creator_headers, json={
        "incident_type": "ACCOUNT_TAKEOVER",
        "platform": "YouTube",
        "occurred_on": date.today().isoformat(),
        "restored_on": date.today().isoformat(),
        "description": "Unauthorized access to the creator account.",
        "recovery_expense": 30000,
        "legal_expense": 10000,
        "revenue_loss": 25000,
    })
    assert created_claim.status_code == 200, created_claim.text
    assert created_claim.json()["claimed_amount"] == 65000
    claim_id = created_claim.json()["id"]
    assert client.post(f"/api/claims/{claim_id}/investigate", headers=creator_headers).status_code == 403
    assert client.post(f"/api/claims/{claim_id}/decision", headers=creator_headers, json={
        "decision": "APPROVE", "reason": "Unauthorized approval attempt",
    }).status_code == 403

    adjuster_login = client.post("/api/auth/login", json={
        "email": "adjuster@example.com", "password": "Adjuster@123",
    })
    assert adjuster_login.status_code == 200, adjuster_login.text
    adjuster_headers = {"Authorization": f"Bearer {adjuster_login.json()['token']}"}
    assert client.post(f"/api/claims/{claim_id}/decision", headers=adjuster_headers, json={
        "decision": "APPROVE", "reason": "Invalid state approval attempt",
    }).status_code == 409

    second_creator = client.post("/api/auth/register", json={
        "email": "other.creator@example.test", "password": "AnotherStrongPass123",
        "full_name": "Other Creator", "business_name": "Other Studio",
        "platform": "Instagram", "handle": "@other",
    })
    other_headers = {"Authorization": f"Bearer {second_creator.json()['token']}"}
    assert client.get(f"/api/claims/{claim_id}", headers=other_headers).status_code == 404
    assert client.get(f"/api/policies/{bound.json()['policy']['id']}", headers=other_headers).status_code == 404
    rejected_fnol = client.post("/api/claims/fnol", headers=other_headers, json={
        "incident_type": "ACCOUNT_TAKEOVER", "platform": "Instagram",
        "occurred_on": date.today().isoformat(), "description": "Account compromise needs a new policy.",
        "recovery_expense": 10000,
    })
    assert rejected_fnol.status_code == 400
    assert client.get("/api/claims", headers=other_headers).json() == []
    new_creator_quote = client.post("/api/quotes", headers=other_headers, json={
        "requested_limit": 150000, "platform": "Instagram",
    })
    assert new_creator_quote.status_code == 200
    assert new_creator_quote.json()["underwriting"] == "STANDARD"
    assert new_creator_quote.json()["security_score"] == 25
    assert new_creator_quote.json()["premium"] > 7200
    selected_policy = client.post("/api/policies/bind", headers=other_headers, json={
        "requested_limit": 150000, "platform": "Instagram",
    })
    assert selected_policy.status_code == 200, selected_policy.text
    policy_activated = client.post(
        f"/api/billing/invoices/{selected_policy.json()['invoice_id']}/pay",
        headers=other_headers,
    )
    assert policy_activated.status_code == 200
    assert policy_activated.json()["policy_status"] == "ACTIVE"
    assert client.post("/api/quotes", headers=other_headers, json={
        "requested_limit": 250000, "platform": "Instagram",
    }).json()["underwriting"] == "REFER"
    assert client.post("/api/quotes", headers=other_headers, json={
        "requested_limit": 350000, "platform": "Instagram",
    }).json()["underwriting"] == "DECLINE"
    new_creator_claim = client.post("/api/claims/fnol", headers=other_headers, json={
        "incident_type": "ACCOUNT_TAKEOVER",
        "platform": "Instagram",
        "occurred_on": date.today().isoformat(),
        "description": "A new policyholder reports an unauthorized account login.",
        "recovery_expense": 10000,
    })
    assert new_creator_claim.status_code == 200, new_creator_claim.text

    for evidence_type, file_name, amount in [
        ("Recovery Invoice", "recovery-invoice.pdf", 30000),
        ("Legal Counsel Invoice", "legal-invoice.pdf", 10000),
        ("Revenue Statement", "revenue-statement.pdf", 25000),
        ("Platform Security Alert", "security-alert.pdf", None),
    ]:
        evidence = client.post(f"/api/claims/{claim_id}/evidence", headers=creator_headers, json={
            "evidence_type": evidence_type,
            "file_name": file_name,
            "notes": "Submitted for adjuster verification.",
        })
        assert evidence.status_code == 200 and evidence.json()["status"] == "PENDING"
        verification_body = {"verified": True, "reason": "Document is clear and consistent with the report."}
        if amount is not None:
            verification_body["verified_amount"] = amount
            assert client.post(
                f"/api/claims/{claim_id}/evidence/{evidence.json()['id']}/verify",
                headers=adjuster_headers,
                json={"verified": True, "reason": "Amount was not provided."},
            ).status_code == 422
        verified = client.post(
            f"/api/claims/{claim_id}/evidence/{evidence.json()['id']}/verify",
            headers=adjuster_headers,
            json=verification_body,
        )
        assert verified.status_code == 200 and verified.json()["status"] == "VERIFIED"

    investigation = client.post(f"/api/claims/{claim_id}/investigate", headers=adjuster_headers)
    assert investigation.status_code == 200, investigation.text
    assert investigation.json()["investigation"]["verified_evidence"] is True
    assert "AI recommendation" in investigation.json()["summary"]
    assessment = client.post(f"/api/claims/{claim_id}/assess", headers=adjuster_headers)
    assert assessment.status_code == 200, assessment.text
    assert assessment.json()["status"] == "PENDING_APPROVAL"
    assert assessment.json()["calculation"]["gross_eligible"] == 40000

    approved = client.post(f"/api/claims/{claim_id}/decision", headers=adjuster_headers, json={
        "decision": "APPROVE", "reason": "Verified coverage and eligible loss are within policy limits.",
    })
    assert approved.status_code == 200 and approved.json()["status"] == "PAYMENT_PENDING"
    paid = client.post(f"/api/claims/{claim_id}/pay", headers=adjuster_headers)
    assert paid.status_code == 200 and paid.json()["status"] == "PAID"
    closed = client.post(f"/api/claims/{claim_id}/close", headers=adjuster_headers)
    assert closed.status_code == 200 and closed.json()["status"] == "CLOSED"
    audit = client.get(f"/api/audit/Claim/{claim_id}", headers=creator_headers)
    assert audit.status_code == 200
    assert {event["action"] for event in audit.json()} >= {
        "CLAIM_CREATED", "AI_INVESTIGATION_COMPLETED", "LOSS_ASSESSMENT_COMPLETED",
        "CLAIM_APPROVE", "CLAIM_PAID", "CLAIM_CLOSED",
    }

    followup_claim = client.post("/api/claims/fnol", headers=creator_headers, json={
        "incident_type": "ACCOUNT_TAKEOVER",
        "platform": "YouTube",
        "occurred_on": date.today().isoformat(),
        "description": "Unauthorized login needs additional review.",
        "recovery_expense": 10000,
        "legal_expense": 0,
        "revenue_loss": 0,
    })
    followup_id = followup_claim.json()["id"]
    requested = client.post(f"/api/claims/{followup_id}/decision", headers=adjuster_headers, json={
        "decision": "REQUEST_INFORMATION", "reason": "Please provide the platform security notification.",
    })
    assert requested.status_code == 200 and requested.json()["status"] == "EVIDENCE_REQUIRED"
    added = client.post(f"/api/claims/{followup_id}/evidence", headers=creator_headers, json={
        "evidence_type": "Platform Security Alert",
        "file_name": "additional-security-alert.pdf",
        "notes": "Platform alert reference.",
    })
    assert added.status_code == 200
    assert client.get(f"/api/claims/{followup_id}", headers=creator_headers).json()["status"] == "INVESTIGATION"
    client.post(f"/api/claims/{followup_id}/investigate", headers=adjuster_headers)
    missing_proof = client.post(f"/api/claims/{followup_id}/assess", headers=adjuster_headers)
    assert missing_proof.status_code == 200
    assert missing_proof.json()["decision"] == "EVIDENCE_REQUIRED"
    exclusion = client.post(f"/api/claims/{followup_id}/exclusion", headers=adjuster_headers, json={
        "code": "PRE_EXISTING_INCIDENT", "reason": "Evidence indicates the incident pre-dates coverage.",
    })
    assert exclusion.status_code == 200 and exclusion.json()["exclusion_code"] == "PRE_EXISTING_INCIDENT"
    blocked = client.post(f"/api/claims/{followup_id}/assess", headers=adjuster_headers)
    assert blocked.status_code == 200 and blocked.json()["decision"] == "HUMAN_REVIEW"
    assert blocked.json()["status"] == "COVERAGE_REVIEW"
    denied_followup = client.post(f"/api/claims/{followup_id}/decision", headers=adjuster_headers, json={
        "decision": "DENY", "reason": "The incident is excluded as pre-existing.",
    })
    assert denied_followup.status_code == 200 and denied_followup.json()["status"] == "DENIED"

    seed_claim = next(claim for claim in client.get("/api/claims", headers=adjuster_headers).json() if claim["number"] == "CLM-CS-1001")
    denied = client.post(f"/api/claims/{seed_claim['id']}/decision", headers=adjuster_headers, json={
        "decision": "DENY", "reason": "Demonstration denial decision with documented rationale.",
    })
    assert denied.status_code == 200 and denied.json()["status"] == "DENIED"
    assert client.post(f"/api/claims/{seed_claim['id']}/close", headers=adjuster_headers).status_code == 200
