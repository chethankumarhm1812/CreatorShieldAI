# Insurance Workflow

## Quote
Creator registers a profile and platform account, then selects a coverage limit and requests a quote. A demonstration premium calculation uses the account security score and requested limit. Limits up to ₹200,000 receive standard terms even for new creators with a low security score; the score affects the indicative premium and is shown as a warning. Limits above ₹200,000 and up to ₹300,000 require underwriter review, and limits above ₹300,000 are declined. Referred/declined quotes cannot be self-bound.

## Policy lifecycle
Quote -> Bind -> Billing account/invoice -> Premium payment -> Active. A bound policy is not active until premium is recorded. Renewal, endorsement and cancellation are future simulator extensions.

## FNOL
Creator reports incident type, platform, incident/restoration dates, narrative and claimed exposures. The system creates an incident and a claim under the active policy. Claimed amounts are not eligibility decisions.

## Claim exposures
A single incident can create multiple exposures:
- RECOVERY
- LEGAL
- INTERRUPTION
- RESTORATION

Each exposure is evaluated against its own coverage limit and requires adjuster-verified financial evidence. A creator-provided filename/reference is not treated as verified proof or an uploaded file.

## Adjudication
Evidence review -> AI investigation -> deterministic policy rules -> transparent loss assessment -> human adjuster -> simulated payment -> closure.

## Example
A covered account takeover has ₹30,000 adjuster-verified recovery expense, ₹10,000 verified legal expense and five elapsed interruption days at ₹5,000/day. With a one-day waiting period, four days (₹20,000) are eligible. Gross eligible loss is ₹60,000. A ₹5,000 deductible produces an illustrative ₹55,000 payout, subject to policy wording and limits.
