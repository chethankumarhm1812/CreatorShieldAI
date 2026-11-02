from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.models import *
from ..schemas.schemas import *
from ..security import current_user, verify_password, create_token, require_roles, hash_password
from ..services.core import audit
from ..rules.policy_rules import evaluate_policy, calculate_loss, can_transition
from ..agents.graph import run_claim_agents

router = APIRouter()

def require_policy_access(policy, user):
    if user.role == "CREATOR" and (not user.creator or policy.creator_id != user.creator.id):
        raise HTTPException(404, "Policy not found")

def require_claim_access(claim, user):
    if user.role == "CREATOR" and (not user.creator or claim.policy.creator_id != user.creator.id):
        raise HTTPException(404, "Claim not found")

def move_claim(claim, target):
    if claim.status == target:
        return
    if not can_transition(claim.status, target):
        raise HTTPException(409, f"Claim cannot move from {claim.status} to {target}")
    claim.status = target

@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email).first()
    if not user or not verify_password(body.password, user.password_hash): raise HTTPException(401,"Invalid credentials")
    return {"token": create_token(user), "user": {"id":user.id,"name":user.full_name,"email":user.email,"role":user.role}}

@router.post("/auth/register")
def register(body:RegisterRequest,db:Session=Depends(get_db)):
    email=body.email.strip().lower()
    if "@" not in email or "." not in email.rsplit("@",1)[-1]:
        raise HTTPException(422,"Enter a valid email address")
    if db.query(User).filter(func.lower(User.email)==email).first():
        raise HTTPException(409,"An account with this email already exists")
    user=User(email=email,password_hash=hash_password(body.password),role="CREATOR",full_name=body.full_name.strip())
    db.add(user)
    db.flush()
    creator=Creator(user_id=user.id,business_name=body.business_name.strip(),creator_type=body.creator_type.strip(),mfa_enabled=body.mfa_enabled,recovery_email=body.recovery_email,backup_auth=body.backup_auth)
    db.add(creator)
    db.flush()
    security_score=25+25*sum((creator.mfa_enabled,creator.recovery_email,creator.backup_auth))
    account=CreatorAccount(creator_id=creator.id,platform=body.platform.strip(),handle=body.handle.strip(),monetized=True,security_score=security_score)
    db.add(account)
    audit(db,user,"CREATOR_REGISTERED","Creator",creator.id,body.email)
    audit(db,user,"ACCOUNT_ADDED","CreatorAccount",account.id,f"{account.platform}:{account.handle}")
    db.commit()
    return {"token":create_token(user),"user":{"id":user.id,"name":user.full_name,"email":user.email,"role":user.role}}

@router.get("/me")
def me(user=Depends(current_user)):
    return {"id":user.id,"name":user.full_name,"email":user.email,"role":user.role}

@router.get("/accounts")
def accounts(user=Depends(current_user),db:Session=Depends(get_db)):
    query=db.query(CreatorAccount)
    if user.role=="CREATOR":
        if not user.creator:return []
        query=query.filter(CreatorAccount.creator_id==user.creator.id)
    return [{"id":item.id,"platform":item.platform,"handle":item.handle,"monetized":item.monetized,"security_score":item.security_score} for item in query.order_by(CreatorAccount.id.desc()).all()]

@router.post("/accounts")
def add_account(body:AccountCreate,user=Depends(require_roles("CREATOR")),db:Session=Depends(get_db)):
    creator=user.creator
    if not creator:raise HTTPException(400,"Creator profile is required")
    handle=body.handle.strip()
    duplicate=db.query(CreatorAccount).filter(CreatorAccount.creator_id==creator.id,func.lower(CreatorAccount.platform)==body.platform.lower(),func.lower(CreatorAccount.handle)==handle.lower()).first()
    if duplicate:raise HTTPException(409,"This platform account is already registered")
    security_score=25+25*sum((creator.mfa_enabled,creator.recovery_email,creator.backup_auth))
    item=CreatorAccount(creator_id=creator.id,platform=body.platform.strip(),handle=handle,monetized=body.monetized,security_score=security_score)
    db.add(item)
    db.flush()
    audit(db,user,"ACCOUNT_ADDED","CreatorAccount",item.id,f"{item.platform}:{item.handle}")
    db.commit()
    return {"id":item.id,"platform":item.platform,"handle":item.handle,"monetized":item.monetized,"security_score":item.security_score}

@router.get("/dashboard")
def dashboard(user=Depends(current_user), db: Session=Depends(get_db)):
    if user.role == "CREATOR":
        c=user.creator; p=c.policies[0] if c and c.policies else None
        claims=db.query(Claim).join(Policy).filter(Policy.creator_id==c.id).all() if c else []
        return {"role":"CREATOR","creator":c.business_name,"security_score":max([a.security_score for a in c.accounts], default=0),"policy":policy_json(p) if p else None,"claims":len(claims),"open_claims":sum(x.status not in {"PAID","CLOSED","DENIED"} for x in claims)}
    return {"role":"ADJUSTER","metrics":{"active_policies":db.query(Policy).filter(Policy.status=="ACTIVE").count(),"open_claims":db.query(Claim).filter(~Claim.status.in_(["PAID","CLOSED","DENIED"])).count(),"pending_approval":db.query(Claim).filter(Claim.status=="PENDING_APPROVAL").count(),"total_exposure":float(db.query(func.coalesce(func.sum(Claim.eligible_amount),0)).scalar() or 0),"premium_collected":float(db.query(func.coalesce(func.sum(Invoice.amount),0)).filter(Invoice.status=="PAID").scalar() or 0)}}

def policy_json(p):
    if not p:return None
    return {"id":p.id,"number":p.policy_number,"status":p.status,"product":p.product_name,"effective":str(p.effective_date),"expiry":str(p.expiry_date),"premium":p.premium,"aggregate_limit":p.aggregate_limit,"deductible":p.deductible,"waiting_days":p.waiting_days,"coverages":[{"code":x.code,"name":x.name,"limit":x.limit_amount,"daily_benefit":x.daily_benefit} for x in p.coverages]}

@router.get("/policies")
def policies(user=Depends(current_user), db: Session=Depends(get_db)):
    q=db.query(Policy)
    if user.role=="CREATOR": q=q.filter(Policy.creator_id==user.creator.id)
    return [policy_json(p) for p in q.all()]

@router.get("/policies/{policy_id}")
def policy_detail(policy_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.get(Policy,policy_id)
    if not p:raise HTTPException(404,"Policy not found")
    require_policy_access(p, user)
    return policy_json(p)

@router.post("/quotes")
def quote(body:QuoteRequest,user=Depends(require_roles("CREATOR")),db:Session=Depends(get_db)):
    creator = user.creator
    actual_score = max((account.security_score for account in creator.accounts), default=0) if creator else 0
    factor=1 + max(0,70-actual_score)/200
    premium=round(7200*(body.requested_limit/150000)*factor,2)
    outcome = "DECLINE" if body.requested_limit > 300000 else ("REFER" if body.requested_limit > 200000 else "STANDARD")
    if outcome == "DECLINE":
        reason = "Requested limit exceeds the simulator's maximum."
    elif outcome == "REFER":
        reason = "Requested limit requires underwriter review. Choose a limit of ₹200,000 or less for an instant policy offer."
    elif actual_score < 70:
        reason = "Available on standard terms. The lower account security score increases the indicative premium; improving security controls may reduce future premiums."
    else:
        reason = "Within configured demonstration underwriting thresholds."
    return {"premium":premium,"requested_limit":body.requested_limit,"security_score":actual_score,"underwriting":outcome,"reason":reason,"platform":body.platform}

@router.post("/policies/bind")
def bind_policy(body:QuoteRequest,user=Depends(require_roles("CREATOR")),db:Session=Depends(get_db)):
    result = quote(body, user, db)
    if result["underwriting"] != "STANDARD":
        raise HTTPException(422, result["reason"])
    creator = user.creator
    if not creator:
        raise HTTPException(400, "Creator profile is required before binding coverage")
    policy_number = f"CS-{date.today():%Y%m%d}-{db.query(Policy).count()+1:04d}"
    policy = Policy(
        policy_number=policy_number,
        creator_id=creator.id,
        status="BOUND",
        effective_date=date.today(),
        expiry_date=date.today()+timedelta(days=365),
        premium=result["premium"],
        aggregate_limit=body.requested_limit,
        deductible=5000,
        waiting_days=1,
    )
    policy.coverages = [
        PolicyCoverage(code="RECOVERY", name="Account Recovery Expenses", limit_amount=min(50000, body.requested_limit)),
        PolicyCoverage(code="INTERRUPTION", name="Revenue Interruption", limit_amount=min(75000, body.requested_limit), daily_benefit=5000),
        PolicyCoverage(code="LEGAL", name="Cyber Legal Assistance", limit_amount=min(50000, body.requested_limit)),
        PolicyCoverage(code="RESTORATION", name="Creator Business Restoration", limit_amount=min(25000, body.requested_limit)),
    ]
    db.add(policy)
    db.flush()
    account = BillingAccount(
        policy_id=policy.id,
        account_number=f"BA-{policy_number}",
        billing_status="OUTSTANDING",
        next_due=date.today()+timedelta(days=14),
        outstanding=result["premium"],
    )
    db.add(account)
    db.flush()
    invoice = Invoice(
        billing_account_id=account.id,
        invoice_number=f"INV-{policy_number}",
        amount=result["premium"],
        due_date=account.next_due,
        status="DUE",
    )
    db.add(invoice)
    audit(db,user,"POLICY_BOUND","Policy",policy.id,f"Underwriting: {result['underwriting']}")
    audit(db,user,"INVOICE_GENERATED","Invoice",invoice.invoice_number,str(result["premium"]))
    db.commit()
    return {"policy":policy_json(policy),"billing_account":account.account_number,"invoice_number":invoice.invoice_number,"invoice_id":invoice.id}

@router.get("/billing")
def billing(user=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(BillingAccount)
    if user.role=="CREATOR":q=q.join(Policy).filter(Policy.creator_id==user.creator.id)
    out=[]
    for b in q.all(): out.append({"account_number":b.account_number,"status":b.billing_status,"next_due":str(b.next_due),"outstanding":b.outstanding,"invoices":[{"id":i.id,"number":i.invoice_number,"amount":i.amount,"due":str(i.due_date),"status":i.status,"payments":[{"amount":p.amount,"status":p.status,"reference":p.reference,"date":p.processed_at.isoformat() if p.processed_at else None} for p in i.payments]} for i in b.invoices]})
    return out

@router.post("/billing/invoices/{invoice_id}/pay")
def pay_invoice(invoice_id:int,user=Depends(require_roles("CREATOR")),db:Session=Depends(get_db)):
    invoice=db.get(Invoice,invoice_id)
    if not invoice:raise HTTPException(404,"Invoice not found")
    account=invoice.billing_account
    policy=account.policy
    require_policy_access(policy,user)
    if invoice.status=="PAID":
        raise HTTPException(409,"Invoice is already paid")
    if invoice.status not in {"DUE","PAST_DUE"}:
        raise HTTPException(409,"Invoice cannot be paid in its current status")
    payment=BillingPayment(invoice_id=invoice.id,amount=invoice.amount,status="PAID",reference=f"BILL-PAY-{invoice.id}-{int(datetime.now(timezone.utc).timestamp())}")
    invoice.status="PAID"
    policy.status="ACTIVE"
    account.outstanding=max(0.0,account.outstanding-invoice.amount)
    account.billing_status="CURRENT" if account.outstanding==0 else "OUTSTANDING"
    audit(db,user,"PREMIUM_PAYMENT_RECEIVED","Invoice",invoice.invoice_number,payment.reference)
    db.add(payment)
    db.commit()
    return {"invoice_number":invoice.invoice_number,"payment_reference":payment.reference,"status":invoice.status,"policy_status":policy.status}

def validate_claim_intake(incident_type,body):
    requested={"RECOVERY":body.recovery_expense,"LEGAL":body.legal_expense,"INTERRUPTION":body.revenue_loss}
    if not any(requested.values()):
        raise HTTPException(422,"Enter at least one claimed expense or revenue loss")
    allowed={"ACCOUNT_TAKEOVER","MALWARE_COMPROMISE","RANSOMWARE"}
    if incident_type not in allowed and (body.recovery_expense or body.legal_expense):
        raise HTTPException(422,"Recovery and legal expenses require a covered compromise incident")

def create_claim_record(incident,policy,intake,user,db):
    requested={"RECOVERY":intake.recovery_expense,"LEGAL":intake.legal_expense,"INTERRUPTION":intake.revenue_loss}
    claim=Claim(claim_number=f"CLM-{date.today():%Y%m%d}-{db.query(Claim).count()+1:04d}",policy_id=policy.id,incident_id=incident.id,status="OPEN",claimed_amount=sum(requested.values()))
    db.add(claim)
    db.flush()
    for code, amount in requested.items():
        if amount <= 0:continue
        db.add(ClaimExposure(claim_id=claim.id, coverage_code=code, claimed_amount=amount, eligible_amount=0))
    audit(db,user,"CLAIM_CREATED","Claim",claim.id)
    return claim

def active_policy(creator):
    return next((policy for policy in creator.policies if policy.status=="ACTIVE"),None)

@router.post("/incidents")
def create_incident(body:IncidentCreate,user=Depends(require_roles("CREATOR")),db:Session=Depends(get_db)):
    creator=user.creator
    if not creator or not active_policy(creator):raise HTTPException(400,"An active policy is required to report an incident")
    incident=Incident(creator_id=creator.id,incident_number=f"INC-{date.today():%Y%m%d}-{db.query(Incident).count()+1:04d}",**body.model_dump())
    db.add(incident);db.flush();audit(db,user,"FNOL_CREATED","Incident",incident.id,body.description);db.commit()
    return {"id":incident.id,"number":incident.incident_number,"status":"FNOL"}

@router.post("/claims/fnol")
def submit_fnol(body:FNOLCreate,user=Depends(require_roles("CREATOR")),db:Session=Depends(get_db)):
    creator=user.creator
    if not creator:raise HTTPException(400,"Creator profile is required to report a claim")
    policy=active_policy(creator)
    if not policy:raise HTTPException(400,"An active policy is required to report a claim")
    intake=ClaimIntake(recovery_expense=body.recovery_expense,legal_expense=body.legal_expense,revenue_loss=body.revenue_loss)
    validate_claim_intake(body.incident_type,intake)
    incident_data=body.model_dump(exclude={"recovery_expense","legal_expense","revenue_loss"})
    incident=Incident(creator_id=creator.id,incident_number=f"INC-{date.today():%Y%m%d}-{db.query(Incident).count()+1:04d}",**incident_data)
    db.add(incident);db.flush();audit(db,user,"FNOL_CREATED","Incident",incident.id,body.description)
    claim=create_claim_record(incident,policy,intake,user,db)
    db.commit()
    return claim_json(claim)

@router.post("/claims/from-incident/{incident_id}")
def create_claim(incident_id:int,body:ClaimIntake=Body(default=ClaimIntake()),user=Depends(require_roles("CREATOR")),db:Session=Depends(get_db)):
    incident=db.get(Incident,incident_id);creator=user.creator
    if not incident or not creator or incident.creator_id!=creator.id:raise HTTPException(404,"Incident not found")
    policy=active_policy(creator)
    if not policy:raise HTTPException(400,"An active policy is required to report a claim")
    validate_claim_intake(incident.incident_type,body)
    claim=create_claim_record(incident,policy,body,user,db)
    db.commit()
    return claim_json(claim)

@router.post("/claims/{claim_id}/evidence")
def add_evidence(claim_id:int,body:EvidenceCreate,user=Depends(current_user),db:Session=Depends(get_db)):
    claim=db.get(Claim,claim_id)
    if not claim:raise HTTPException(404,"Claim not found")
    require_claim_access(claim,user)
    if user.role not in {"CREATOR","ADJUSTER"}:raise HTTPException(403,"Insufficient permissions")
    if claim.status not in {"OPEN","INVESTIGATION","EVIDENCE_REQUIRED"}:raise HTTPException(409,"Evidence cannot be added at this claim stage")
    e=Evidence(claim_id=claim.id,**body.model_dump(),verification_status="PENDING")
    db.add(e)
    if claim.status=="OPEN":
        move_claim(claim,"INITIAL_REVIEW")
        move_claim(claim,"INVESTIGATION")
    elif claim.status=="EVIDENCE_REQUIRED":move_claim(claim,"INVESTIGATION")
    audit(db,user,"EVIDENCE_ADDED","Claim",claim.id,body.file_name)
    db.commit()
    return {"id":e.id,"status":e.verification_status}

@router.post("/claims/{claim_id}/evidence/{evidence_id}/verify")
def verify_claim_evidence(claim_id:int,evidence_id:int,body:EvidenceVerification,user=Depends(require_roles("ADJUSTER")),db:Session=Depends(get_db)):
    claim=db.get(Claim,claim_id)
    if not claim:raise HTTPException(404,"Claim not found")
    evidence=next((item for item in claim.evidences if item.id==evidence_id),None)
    if not evidence:raise HTTPException(404,"Evidence not found")
    needs_amount=any(term in evidence.evidence_type.lower() for term in ("recovery","restoration","technical","legal","lawyer","attorney","counsel","revenue","statement","payout"))
    if body.verified and needs_amount and body.verified_amount is None:
        raise HTTPException(422,"Enter the monetary amount verified from this evidence")
    evidence.verification_status="VERIFIED" if body.verified else "REJECTED"
    evidence.verified_amount=(body.verified_amount or 0) if body.verified else 0
    audit(db,user,"EVIDENCE_VERIFIED" if body.verified else "EVIDENCE_REJECTED","Claim",claim.id,body.reason)
    db.commit()
    return {"id":evidence.id,"status":evidence.verification_status,"verified_amount":evidence.verified_amount}

@router.post("/claims/{claim_id}/exclusion")
def record_exclusion(claim_id:int,body:ExclusionUpdate,user=Depends(require_roles("ADJUSTER")),db:Session=Depends(get_db)):
    claim=db.get(Claim,claim_id)
    if not claim:raise HTTPException(404,"Claim not found")
    if claim.status in {"APPROVED","PAYMENT_PENDING","PAID","DENIED","CLOSED"}:
        raise HTTPException(409,"Exclusion review cannot change a finalized claim")
    claim.incident.exclusion_code=body.code
    audit(db,user,"EXCLUSION_FLAGGED" if body.code else "EXCLUSION_CLEARED","Claim",claim.id,f"{body.code or 'CLEARED'}: {body.reason}")
    if body.code and claim.status=="PENDING_APPROVAL":move_claim(claim,"COVERAGE_REVIEW")
    db.commit()
    return claim_json(claim)

def claim_json(c):
    return {"id":c.id,"number":c.claim_number,"status":c.status,"policy_id":c.policy_id,"policy_number":c.policy.policy_number,"incident_id":c.incident_id,"incident_type":c.incident.incident_type,"incident_date":str(c.incident.occurred_on),"platform":c.incident.platform,"exclusion_code":c.incident.exclusion_code,"claimed_amount":c.claimed_amount,"eligible_amount":c.eligible_amount,"recommended_payout":c.recommended_payout,"risk_level":c.risk_level,"reason":c.decision_reason,"evidence":[{"id":e.id,"type":e.evidence_type,"file":e.file_name,"status":e.verification_status,"verified_amount":e.verified_amount,"notes":e.notes} for e in c.evidences],"exposures":[{"id":x.id,"coverage":x.coverage_code,"claimed":x.claimed_amount,"eligible":x.eligible_amount,"status":x.status} for x in c.exposures],"assessments":[{"agent":a.agent_name,"findings":a.findings,"confidence":a.confidence,"recommendation":a.recommendation} for a in c.assessments],"payment":{"amount":c.payment.amount,"status":c.payment.status,"reference":c.payment.reference} if c.payment else None}

@router.get("/claims")
def claims(user=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Claim).join(Policy)
    if user.role=="CREATOR":q=q.filter(Policy.creator_id==user.creator.id)
    return [claim_json(c) for c in q.order_by(Claim.created_at.desc()).all()]

@router.get("/claims/{claim_id}")
def claim_detail(claim_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c:raise HTTPException(404,"Claim not found")
    require_claim_access(c,user)
    return claim_json(c)

def has_exposure_evidence(claim, code):
    names=[e.evidence_type.lower() for e in claim.evidences if e.verification_status=="VERIFIED"]
    matches={
        "RECOVERY":("recovery","restoration","technical","incident-response"),
        "LEGAL":("legal","lawyer","attorney","counsel"),
        "INTERRUPTION":("revenue","statement","platform payout"),
        "RESTORATION":("recovery","restoration","technical","incident-response"),
    }
    required=matches.get(code,())
    return any(term in name for name in names for term in required)

def verified_exposure_amount(claim, code):
    names=[e for e in claim.evidences if e.verification_status=="VERIFIED"]
    matches={
        "RECOVERY":("recovery","restoration","technical","incident-response"),
        "LEGAL":("legal","lawyer","attorney","counsel"),
        "INTERRUPTION":("revenue","statement","platform payout"),
        "RESTORATION":("recovery","restoration","technical","incident-response"),
    }
    required=matches.get(code,())
    return sum(float(item.verified_amount or 0) for item in names if any(term in item.evidence_type.lower() for term in required))

@router.post("/claims/{claim_id}/investigate")
def investigate_claim(claim_id:int,user=Depends(require_roles("ADJUSTER")),db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c:raise HTTPException(404,"Claim not found")
    allowed={"OPEN","INITIAL_REVIEW","INVESTIGATION","EVIDENCE_REQUIRED","PENDING_APPROVAL"}
    if c.status not in allowed:raise HTTPException(409,"Investigation cannot run at this claim stage")
    incident={"incident_type":c.incident.incident_type,"platform":c.incident.platform,"description":c.incident.description}
    evidence=[{"type":e.evidence_type,"notes":e.notes,"verification_status":e.verification_status,"verified_amount":e.verified_amount} for e in c.evidences]
    result=run_claim_agents(incident,evidence)
    c.risk_level=result["risk"]["level"]
    for name,key in [("Incident Triage Agent","triage"),("Evidence Investigation Agent","investigation"),("Risk Review Agent","risk"),("Claim Summary Agent","summary")]:
        data=result[key];findings=str(data);rec=data.get("recommendation","PROCEED") if isinstance(data,dict) else "PROCEED"
        db.add(AgentAssessment(claim_id=c.id,agent_name=name,findings=findings,confidence=float(data.get("confidence",.9)) if isinstance(data,dict) else .9,recommendation=rec))
    if c.status=="OPEN":
        move_claim(c,"INITIAL_REVIEW")
        move_claim(c,"INVESTIGATION")
    elif c.status in {"INITIAL_REVIEW","EVIDENCE_REQUIRED"}:
        move_claim(c,"INVESTIGATION")
    audit(db,user,"AI_INVESTIGATION_COMPLETED","Claim",c.id,result.get("summary",""))
    db.commit()
    return {"summary":result.get("summary"),"triage":result.get("triage"),"investigation":result.get("investigation"),"risk":result.get("risk")}

@router.post("/claims/{claim_id}/assess")
def assess_claim(claim_id:int,user=Depends(require_roles("ADJUSTER")),db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c:raise HTTPException(404,"Claim not found")
    if c.status not in {"INVESTIGATION","EVIDENCE_REQUIRED","COVERAGE_REVIEW","PENDING_APPROVAL"}:raise HTTPException(409,"Coverage cannot be evaluated at this claim stage")
    p=c.policy
    verified_count=sum(e.verification_status=="VERIFIED" for e in c.evidences)
    rules=evaluate_policy(p,c.incident,p.creator,verified_count)
    blocked=[r for r in rules if not r.passed and r.severity=="BLOCK"]
    if blocked:
        c.decision_reason="; ".join(x.message for x in blocked)
        if c.status in {"INVESTIGATION","EVIDENCE_REQUIRED","PENDING_APPROVAL"}:move_claim(c,"COVERAGE_REVIEW")
        audit(db,user,"COVERAGE_BLOCKED","Claim",c.id,c.decision_reason)
        db.commit()
        return {"decision":"HUMAN_REVIEW","rules":[r.__dict__ for r in rules],"status":c.status}
    missing=[x.coverage_code for x in c.exposures if not has_exposure_evidence(c,x.coverage_code) or verified_exposure_amount(c,x.coverage_code)<=0]
    if verified_count<2:missing.append("MINIMUM_VERIFIED_EVIDENCE")
    if missing:
        c.decision_reason="Verified evidence is required for: "+", ".join(sorted(set(missing)))
        if c.status!="EVIDENCE_REQUIRED":move_claim(c,"EVIDENCE_REQUIRED")
        audit(db,user,"EVIDENCE_REQUIRED","Claim",c.id,c.decision_reason)
        db.commit()
        return {"decision":"EVIDENCE_REQUIRED","missing":sorted(set(missing)),"rules":[r.__dict__ for r in rules],"status":c.status}
    if c.status=="INVESTIGATION":move_claim(c,"COVERAGE_REVIEW")
    if c.status=="EVIDENCE_REQUIRED":move_claim(c,"COVERAGE_REVIEW")
    if c.status=="COVERAGE_REVIEW":move_claim(c,"LOSS_ASSESSMENT")
    exposures=[]
    for x in c.exposures:
        coverage=next((cv for cv in p.coverages if cv.code==x.coverage_code),None)
        exposures.append({
            "coverage":x.coverage_code,
            "claimed":x.claimed_amount,
            "limit":coverage.limit_amount if coverage else 0,
            "daily_benefit":coverage.daily_benefit if coverage else 0,
            "days":max(0,((c.incident.restored_on or date.today())-c.incident.occurred_on).days),
            "waiting_days":p.waiting_days,
            "verified":has_exposure_evidence(c,x.coverage_code),
            "verified_amount":verified_exposure_amount(c,x.coverage_code),
        })
    calc=calculate_loss(p,c.incident,exposures)
    for exposure, detail in zip(c.exposures,calc["details"]):
        exposure.eligible_amount=detail["eligible"]
        exposure.status="ELIGIBLE" if detail["eligible"]>0 else "NOT_ELIGIBLE"
    c.claimed_amount=sum(x["claimed"] for x in exposures)
    c.eligible_amount=calc["gross_eligible"]
    c.recommended_payout=calc["payout"]
    if c.status=="LOSS_ASSESSMENT":move_claim(c,"PENDING_APPROVAL")
    elif c.status!="PENDING_APPROVAL":move_claim(c,"PENDING_APPROVAL")
    c.decision_reason="Loss assessment completed; final decision requires an authorized adjuster."
    audit(db,user,"COVERAGE_EVALUATED","Claim",c.id,str([r.__dict__ for r in rules]))
    audit(db,user,"LOSS_ASSESSMENT_COMPLETED","Claim",c.id,str(calc))
    db.commit()
    return {"rules":[r.__dict__ for r in rules],"calculation":calc,"status":c.status}

@router.post("/claims/{claim_id}/decision")
def decision(claim_id:int,body:DecisionCreate,user=Depends(require_roles("ADJUSTER")),db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c:raise HTTPException(404,"Claim not found")
    d=body.decision.upper()
    if d not in {"APPROVE","DENY","REQUEST_INFORMATION"}:raise HTTPException(400,"Invalid decision")
    if d=="APPROVE":
        if c.status!="PENDING_APPROVAL":raise HTTPException(409,"Claim must pass coverage and loss assessment before approval")
        rules=evaluate_policy(c.policy,c.incident,c.policy.creator,sum(e.verification_status=="VERIFIED" for e in c.evidences))
        if any(not rule.passed and rule.severity=="BLOCK" for rule in rules) or any(not rule.passed and rule.code=="MIN_EVIDENCE" for rule in rules) or any(not has_exposure_evidence(c,x.coverage_code) or verified_exposure_amount(c,x.coverage_code)<=0 for x in c.exposures):
            raise HTTPException(409,"Coverage rules or exposure evidence do not permit approval")
        move_claim(c,"APPROVED")
        move_claim(c,"PAYMENT_PENDING")
    elif d=="DENY":
        if c.status not in {"PENDING_APPROVAL","COVERAGE_REVIEW"}:raise HTTPException(409,"Claim must be under coverage or adjuster review before denial")
        move_claim(c,"DENIED")
    else:
        if c.status not in {"OPEN","INITIAL_REVIEW","INVESTIGATION","COVERAGE_REVIEW","LOSS_ASSESSMENT","PENDING_APPROVAL"}:raise HTTPException(409,"Information cannot be requested at this claim stage")
        move_claim(c,"EVIDENCE_REQUIRED")
    c.decision_reason=body.reason
    db.add(ClaimDecision(claim_id=c.id,actor_role=user.role,decision=d,reason=body.reason))
    audit(db,user,f"CLAIM_{d}","Claim",c.id,body.reason)
    db.commit()
    return claim_json(c)

@router.post("/claims/{claim_id}/pay")
def pay(claim_id:int,user=Depends(require_roles("ADJUSTER")),db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c:raise HTTPException(404,"Claim not found")
    if c.status!="PAYMENT_PENDING":raise HTTPException(400,"Claim must be approved before payment")
    p=c.payment or ClaimPayment(claim_id=c.id)
    p.amount=c.recommended_payout;p.status="PAID";p.reference=p.reference or f"PAY-CS-{c.id:05d}";p.processed_at=datetime.now(timezone.utc);db.add(p);move_claim(c,"PAID");audit(db,user,"CLAIM_PAID","Claim",c.id,str(p.amount));db.commit();return claim_json(c)

@router.post("/claims/{claim_id}/close")
def close_claim(claim_id:int,user=Depends(require_roles("ADJUSTER")),db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c:raise HTTPException(404,"Claim not found")
    if c.status not in {"PAID","DENIED"}:raise HTTPException(409,"Only paid or denied claims can be closed")
    move_claim(c,"CLOSED")
    audit(db,user,"CLAIM_CLOSED","Claim",c.id,c.decision_reason)
    db.commit()
    return claim_json(c)

@router.get("/audit/{entity_type}/{entity_id}")
def audit_log(entity_type:str,entity_id:str,user=Depends(current_user),db:Session=Depends(get_db)):
    if user.role=="CREATOR" and entity_type.lower()=="claim":
        claim=db.get(Claim,int(entity_id))
        if not claim:raise HTTPException(404,"Claim not found")
        require_claim_access(claim,user)
    if user.role=="CREATOR" and entity_type.lower()=="policy":
        policy=db.get(Policy,int(entity_id))
        if not policy:raise HTTPException(404,"Policy not found")
        require_policy_access(policy,user)
    return [{"actor":a.actor,"role":a.role,"action":a.action,"details":a.details,"timestamp":a.created_at.isoformat()} for a in db.query(AuditEvent).filter_by(entity_type=entity_type,entity_id=entity_id).order_by(AuditEvent.created_at.desc()).all()]
