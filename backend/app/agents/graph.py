from typing import TypedDict, Any
from datetime import date
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False

class ClaimState(TypedDict, total=False):
    incident: dict
    evidence: list[dict]
    triage: dict
    investigation: dict
    risk: dict
    loss: dict
    summary: str

def triage(state):
    i = state["incident"]
    t = {"category": i["incident_type"], "severity": "HIGH" if i["incident_type"] in {"ACCOUNT_TAKEOVER","RANSOMWARE"} else "MEDIUM", "confidence": 0.94}
    return {"triage": t}

def investigate(state):
    ev = state.get("evidence", [])
    verified_items = [item for item in ev if item.get("verification_status") == "VERIFIED"]
    sufficient = len(verified_items) >= 2
    return {"investigation": {"verified_evidence": sufficient, "verified_count": len(verified_items), "missing": [] if sufficient else ["Platform security notification", "Recovery/support record"], "findings": "At least two evidence items are adjuster-verified." if sufficient else "Additional adjuster-verified evidence is required before final adjudication."}}

def risk(state):
    ev = state.get("evidence", [])
    high = any("duplicate" in (x.get("notes", "").lower()) for x in ev)
    return {"risk": {"level": "HIGH" if high else "LOW", "flags": ["DUPLICATE_EVIDENCE"] if high else [], "recommendation": "REFER" if high else "PROCEED"}}

def summarize(state):
    t, inv, r = state.get("triage",{}), state.get("investigation",{}), state.get("risk",{})
    return {"summary": f"Incident classified as {t.get('category','UNKNOWN')}. Evidence verified: {inv.get('verified_evidence',False)}. Risk: {r.get('level','LOW')}. AI recommendation: {r.get('recommendation','PROCEED')}."}

def run_claim_agents(incident: dict, evidence: list[dict]):
    initial = {"incident": incident, "evidence": evidence}
    if LANGGRAPH_AVAILABLE:
        graph = StateGraph(ClaimState)
        graph.add_node("triage_step", triage)
        graph.add_node("investigation_step", investigate)
        graph.add_node("risk_review_step", risk)
        graph.add_node("summary_step", summarize)
        graph.set_entry_point("triage_step")
        graph.add_edge("triage_step", "investigation_step")
        graph.add_edge("investigation_step", "risk_review_step")
        graph.add_edge("risk_review_step", "summary_step")
        graph.add_edge("summary_step", END)
        result = graph.compile().invoke(initial)
    else:
        result = initial | triage(initial)
        result.update(investigate(result)); result.update(risk(result)); result.update(summarize(result))
    return result
