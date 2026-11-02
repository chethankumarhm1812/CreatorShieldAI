# Guidewire-inspired simulator mapping

This project has no licensed Guidewire environment and is not Guidewire software. These modules model domain responsibilities locally and are replaceable integration boundaries.

| Simulator | Guidewire concept |
|---|---|
| PolicyCenter Simulator | Policy administration, product, quote, underwriting and policy lifecycle |
| ClaimCenter Simulator | FNOL, claim, exposures, evidence, investigation, adjudication and settlement |
| BillingCenter Simulator | Billing account, invoice, payment and outstanding balance |
| Policy rules engine | Business rules / Gosu-style deterministic logic |
| React workflows | PCF-inspired operational screens |
| FastAPI REST API | External integration boundary |
| SQLAlchemy models | Local persistence for a PostgreSQL-ready domain |

## Reference artifacts only

`guidewire/gosu/` and `guidewire/pcf/` contain illustrative examples for interview discussion. They are not compiled, deployed or validated against a licensed Guidewire runtime.

Illustrative Gosu-style rule:

```gosu
// Reference only; not compiled by this project.
function isIncidentWithinPolicyPeriod(policy : Policy, incidentDate : Date) : boolean {
  return policy.Status == "ACTIVE"
      and incidentDate >= policy.EffectiveDate
      and incidentDate <= policy.ExpirationDate
}
```

Illustrative PCF-style workbench concept:

```xml
<!-- Reference only; not a licensed Guidewire PCF artifact. -->
<Screen id="CreatorClaimWorkbench">
  <Panel title="Claim Summary" binding="Claim"/>
  <Panel title="Exposures and Evidence" binding="Claim.Exposures"/>
  <Panel title="AI Recommendation (Advisory)" binding="Claim.Investigation"/>
  <Panel title="Adjuster Decision" binding="Claim.Decision"/>
</Screen>
```

The local screens deliberately keep AI recommendation separate from adjuster decision and require a reason for human decisions.
