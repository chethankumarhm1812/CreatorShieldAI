# AI investigation workflow

LangGraph executes a deterministic local demonstration graph:

```text
FNOL -> Incident Triage -> Evidence Investigation -> Risk Review -> Claim Summary
```

The graph currently uses transparent demo logic and structured dictionary state. LangGraph node names (`triage_step`, `investigation_step`, `risk_review_step`, `summary_step`) are distinct from the state fields they populate. If LangGraph is unavailable, the same node functions execute sequentially.

## Node outputs

- **Incident triage:** reported incident category, severity and confidence.
- **Evidence investigation:** count of adjuster-verified evidence, missing-item list and findings.
- **Risk review:** risk level, anomaly flags and a proceed/refer recommendation.
- **Claim summary:** human-readable aggregation of upstream findings.

The workflow can organize and recommend only. Coverage eligibility is calculated independently by the deterministic policy rules, and only an authorized adjuster can approve, deny or request information. AI confidence is not treated as proof of coverage or verified financial loss.

The current node implementations do not call an external LLM or inspect uploaded bytes. Production work should add reviewed model providers, evidence extraction, prompt/version management, evaluation datasets, observability and privacy controls before making AI claims about document content.
