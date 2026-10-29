# One purchase, two settled charges

Case: CMP-0001
Source: Fictional demonstration complaint
Status: Open
Category: Duplicate card charge
Priority: High
Intent model score: 48.1% (not causal certainty)
Analysis: gemma:2b + local NLP

## Customer-reported complaint
I paid Rs 2400 at a supermarket once, but my bank statement shows two charges. Both entries are marked completed and the merchant receipt shows only one payment. I contacted support three times and each agent told me to wait. I am frustrated because nobody has given me a case update.

## Unverified working hypothesis
Duplicate capture or an authorization hold beside a settled payment

## Reported evidence
- [F1] I paid Rs 2400 at a supermarket once, but my bank statement shows two charges.
- [F2] Both entries are marked completed and the merchant receipt shows only one payment.
- [F3] I contacted support three times and each agent told me to wait.
- [F4] I am frustrated because nobody has given me a case update.

## Verification checklist
- Are both charges settled, or is one pending?
- Do both entries share a merchant and authorization reference?
- Does the receipt confirm only one purchase?

## Investigation and prevention
- Investigate: Trace both entries before opening a duplicate-payment dispute. (Payments operations)
- Prevent recurrence: Check payment retry idempotency and authorization-release reconciliation after the transaction trace. (Process improvement)

## Additional service-process hypothesis
Case ownership or support handoffs may be weak
Inspect ticket owners, contact history and follow-up timestamps.

## Retrieved demonstration playbooks
- [KB-01] Duplicate card charge: Compare the two entries' settlement status, merchant reference and authorization ID. Two settled entries for one receipt support a duplicate capture; one pending entry may be an authorization hold.
- [KB-13] Repeated support handoffs: Repeated contact without a clear update can indicate weak case ownership or poor handoffs. The complaint establishes only what the customer reports. Review ticket history, assigned owners, follow-up timestamps and the applicable service target before identifying the process failure.
- [KB-06] Pending bank transfer: A transfer marked pending has not reached a confirmed final state. Check submission time, processing status, any review flag and the payment rail's operating window before escalating.

## Local LLM explanation
Model: gemma:2b
Duplicate card charge
Possible cause (unverified): Duplicate capture or an authorization hold beside a settled payment
Why this needs checking: The complaint describes a situation where the customer reports a duplicate charge, but the bank statement shows only one payment. This could indicate a case where the capture or authorization hold was not completed correctly, resulting in a duplicate charge.
Citations: KB-01, KB-13
Exact quotations and retrieved citation IDs checked; causality not verified

## Draft reply for human review
Thank you for reporting this. I understand the issue concerns duplicate card charge. We need to check the transaction or case records before confirming the cause. Our next step is to involve payments operations. Please use the bank's secure channel for the transaction date and a masked reference. Please do not share your PIN, OTP or full card number. We will provide an update after the trace.

Research prototype. Playbooks and demo cases are authored examples. BANKING77 evaluates intent routing only.
Common identifiers are masked; automated masking does not guarantee removal of all sensitive information.