# Guidewire Interview Story

## 30-second pitch

CreatorShield AI is a creator-focused cyber insurance prototype. Because we did not have access to a licensed Guidewire environment, we built a Guidewire-inspired insurance core simulator with separate PolicyCenter, ClaimCenter and BillingCenter domains. The product covers specified account compromise/restriction losses. AI agents assist with incident triage, evidence investigation and loss assessment, while deterministic policy rules control coverage and an authorized human adjuster makes the final consequential decision.

## Questions to expect

1. Why separate policy, claim and billing domains?
2. What belongs in PolicyCenter versus ClaimCenter?
3. Why is billing not part of claim adjudication?
4. Why should AI not decide a claim by itself?
5. How do you prevent a claim from exceeding a coverage limit?
6. How would you model multiple exposures from one incident?
7. How would you implement the rules in Gosu?
8. What would be configured in PCF?
9. How would you integrate the simulator with real Guidewire?
10. How do you audit an AI recommendation?
11. How do you handle duplicate evidence?
12. How would you secure uploaded documents?
13. What happens if a policy expires before the incident?
14. How would renewals work?
15. How would cancellation and billing delinquency interact with coverage?
16. How would you test an insurance rule change?
17. How would you evaluate the AI agents?
18. What is the difference between claimed, eligible and payable amounts?
19. How do you handle human overrides?
20. What would you change for production?

## Strong answer to the Guidewire-access question

We intentionally did not present the simulator as actual Guidewire. The domain boundaries mirror PolicyCenter, ClaimCenter and BillingCenter responsibilities. When a licensed environment becomes available, the simulator adapters can be replaced by real Guidewire configuration, Gosu/PCF customizations and supported APIs/events without redesigning the creator-facing experience or the insurance domain model.
