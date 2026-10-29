# A card payment I did not make

Case: CMP-0003
Source: Fictional demonstration complaint
Status: Open
Category: Unrecognized card payment
Priority: Urgent
Intent model score: 78.2% (not causal certainty)
Analysis: gemma:2b + local NLP

## Customer-reported complaint
There is a card payment for Rs 8600 to a merchant I do not recognize. I did not authorize this transaction and my card is still with me. I am worried about more charges.

## Unverified working hypothesis
Possible unauthorized card use or an unfamiliar merchant descriptor

## Reported evidence
- [F1] There is a card payment for Rs 8600 to a merchant I do not recognize.
- [F2] I did not authorize this transaction and my card is still with me.
- [F3] I am worried about more charges.

## Verification checklist
- Does the customer recognize the merchant's trading name?
- Was a supplementary card or recurring subscription used?
- Has the customer already frozen the affected card?

## Investigation and prevention
- Investigate: Use the bank's secure channel to protect the card and investigate the disputed transaction. (Fraud and disputes)
- Prevent recurrence: Review transaction monitoring and the clarity of merchant descriptors after investigation. (Process improvement)

## Retrieved demonstration playbooks
- [KB-02] Unrecognized card payment: Treat an unrecognized card payment as a security concern. First check the merchant descriptor and any authorized supplementary-card use. If the customer still denies the transaction, route it for a fraud investigation; the complaint itself does not prove fraud.
- [KB-05] Pending card payment: A pending card payment is an authorization, not necessarily a completed debit. Check the merchant capture and authorization-release timestamps. Do not promise a refund or a fixed release time without the applicable bank policy.
- [KB-10] Refund not received: A merchant saying a refund was issued does not establish that it settled. Request the merchant refund reference, initiation date and network trace, then check bank posting. Avoid an unsupported promise about refund timing.

## Local LLM explanation
Model: gemma:2b
There is a card payment for Rs 8600 to a merchant I do not recognize. I did not authorize this transaction and my card is still with me. I am worried about more charges.
Possible cause (unverified): Possible unauthorized card use or an unfamiliar merchant descriptor
Why this needs checking: The complaint describes an unrecognized merchant, which could indicate an unauthorized transaction. Additionally, the customer's concern about more charges suggests suspicious activity.
Citations: KB-02, KB-05
Exact quotations and retrieved citation IDs checked; causality not verified

## Draft reply for human review
Thank you for reporting this. I understand the issue concerns unrecognized card payment. We need to check the transaction or case records before confirming the cause. Our next step is to involve fraud and disputes. Please use the bank's secure channel for the transaction date and a masked reference. Please do not share your PIN, OTP or full card number. We will provide an update after the trace.

Research prototype. Playbooks and demo cases are authored examples. BANKING77 evaluates intent routing only.
Common identifiers are masked; automated masking does not guarantee removal of all sensitive information.