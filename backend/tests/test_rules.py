from types import SimpleNamespace
from datetime import date
from app.rules.policy_rules import evaluate_policy, calculate_loss, can_transition

def test_policy_active_and_covered():
    p=SimpleNamespace(effective_date=date(2026,1,1),expiry_date=date(2027,1,1),status='ACTIVE',deductible=5000,aggregate_limit=150000)
    i=SimpleNamespace(occurred_on=date(2026,10,18),incident_type='ACCOUNT_TAKEOVER')
    c=SimpleNamespace(mfa_enabled=True,recovery_email=True,backup_auth=True)
    rules=evaluate_policy(p,i,c,2)
    assert all(r.passed for r in rules)

def test_loss_cap_and_deductible():
    p=SimpleNamespace(deductible=5000,aggregate_limit=150000)
    calc=calculate_loss(p,None,[{'coverage':'RECOVERY','claimed':70000,'limit':50000},{'coverage':'LEGAL','claimed':10000,'limit':50000}])
    assert calc['gross_eligible']==60000
    assert calc['payout']==55000

def test_revenue_waiting_period_daily_benefit_and_evidence():
    p=SimpleNamespace(deductible=5000,aggregate_limit=100000,waiting_days=2)
    calc=calculate_loss(p,None,[
        {'coverage':'INTERRUPTION','claimed':50000,'limit':75000,'daily_benefit':5000,'days':5,'verified_amount':12000},
        {'coverage':'LEGAL','claimed':10000,'limit':50000,'verified':False},
    ])
    assert calc['details'][0]['covered_days']==3
    assert calc['details'][0]['eligible']==12000
    assert calc['details'][1]['eligible']==0
    assert calc['gross_eligible']==12000
    assert calc['payout']==7000

def test_policy_period_security_and_exclusion_rules():
    p=SimpleNamespace(effective_date=date(2026,1,1),expiry_date=date(2027,1,1),status='ACTIVE',deductible=0,aggregate_limit=100000,waiting_days=1)
    incident=SimpleNamespace(occurred_on=date(2025,12,31),incident_type='ACCOUNT_TAKEOVER',exclusion_code='PRE_EXISTING_INCIDENT')
    creator=SimpleNamespace(mfa_enabled=False,recovery_email=True,backup_auth=False)
    rules=evaluate_policy(p,incident,creator,0)
    by_code={rule.code:rule for rule in rules}
    assert not by_code['POLICY_PERIOD'].passed
    assert by_code['SECURITY_CONTROLS'].severity=='WARN'
    assert not by_code['EXCLUSION_SCREEN'].passed
    assert not by_code['MIN_EVIDENCE'].passed

def test_aggregate_limit_is_applied_across_exposures():
    p=SimpleNamespace(deductible=0,aggregate_limit=60000,waiting_days=0)
    calc=calculate_loss(p,None,[
        {'coverage':'RECOVERY','claimed':50000,'limit':50000},
        {'coverage':'LEGAL','claimed':30000,'limit':30000},
    ])
    assert calc['gross_eligible']==60000
    assert [item['eligible'] for item in calc['details']]==[50000,10000]

def test_claim_state_transitions_reject_skipped_or_terminal_states():
    assert can_transition('PENDING_APPROVAL','APPROVED')
    assert not can_transition('OPEN','PAID')
    assert not can_transition('CLOSED','OPEN')
