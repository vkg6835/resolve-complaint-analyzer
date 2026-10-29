# Recipient still waiting for money

Case: CMP-0002
Source: Fictional demonstration complaint
Status: Under review
Category: Recipient missing transfer
Priority: High
Intent model score: 89.6% (not causal certainty)
Analysis: gemma:2b + local NLP

## Customer-reported complaint
I transferred Rs 12000 to my landlord four days ago. The money has left my account but the recipient says nothing has arrived. The app says the transfer is complete. I contacted support twice and was sent to different agents.

## Unverified working hypothesis
A gap between sending, intermediary processing and beneficiary credit

## Reported evidence
- [F1] I transferred Rs 12000 to my landlord four days ago.
- [F2] The money has left my account but the recipient says nothing has arrived.
- [F3] The app says the transfer is complete.
- [F4] I contacted support twice and was sent to different agents.

## Verification checklist
- Does the sending bank show settlement or only submission?
- Are the recipient account details correct?
- Has the recipient bank acknowledged the transfer reference?

## Investigation and prevention
- Investigate: Start an end-to-end trace using the bank reference and beneficiary acknowledgement. (Transfer investigations)
- Prevent recurrence: Improve beneficiary-credit visibility and handoffs between banks. (Process improvement)

## Additional service-process hypothesis
Case ownership or support handoffs may be weak
Inspect ticket owners, contact history and follow-up timestamps.

## Retrieved demonstration playbooks
- [KB-08] Recipient missing transfer: A sent transfer that is missing at the recipient needs an end-to-end trace. Sender debit does not prove beneficiary credit. Confirm beneficiary details, transfer reference, intermediary status and recipient-bank acknowledgement.
- [KB-13] Repeated support handoffs: Repeated contact without a clear update can indicate weak case ownership or poor handoffs. The complaint establishes only what the customer reports. Review ticket history, assigned owners, follow-up timestamps and the applicable service target before identifying the process failure.
- [KB-09] Incoming transfer missing: If incoming money is missing from the balance, check sender confirmation, account reference, inbound settlement and ledger posting. Sender confirmation alone does not prove funds reached the receiving bank.

## Local LLM explanation
Model: gemma:2b
Recipient missing transfer
Possible cause (unverified): A gap between sending, intermediary processing and beneficiary credit
Why this needs checking: The complaint describes a situation where the recipient says the money has arrived but the app says it is complete, indicating a potential delay in the transfer process.
Citations: KB-08, KB-13
Exact quotations and retrieved citation IDs checked; causality not verified

## Draft reply for human review
Thank you for reporting this. I understand the issue concerns recipient missing transfer. We need to check the transaction or case records before confirming the cause. Our next step is to involve transfer investigations. Please use the bank's secure channel for the transaction date and a masked reference. Please do not share your PIN, OTP or full card number. We will provide an update after the trace.

Research prototype. Playbooks and demo cases are authored examples. BANKING77 evaluates intent routing only.
Common identifiers are masked; automated masking does not guarantee removal of all sensitive information.