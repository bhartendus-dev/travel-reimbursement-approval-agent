# Risks, Controls, and Production Next Steps

## Key Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Stale/incorrect policy | Wrong decision | Version policies, effective-date filters, return policy evidence |
| LLM hallucination | Misleading explanation | Grounded context, structured output, deterministic decision/fallback |
| Prompt injection | Model manipulation | Treat claim/receipt as untrusted data; no decision authority |
| Missing/unreadable receipt | Insufficient evidence | Manual Review |
| Duplicate claim | Potential overpayment | Deterministic duplicate check; Manual Review |
| Validation service outage | Unsafe automation | Fail safe to Manual Review |
| LLM outage | Explanation unavailable | Deterministic fallback |
| Sensitive data exposure | Privacy/compliance issue | Data minimization, encryption, RBAC, redacted logs |
| Incorrect arithmetic | Financial loss | Deterministic unit-tested calculations |
| Excess model cost/latency | Poor economics | Small model, short context, selective LLM use |

## Manual Review Triggers

- missing mandatory receipt
- low receipt extraction confidence
- suspected duplicate
- no applicable policy
- conflicting/ambiguous policy
- high-value threshold
- mandatory validation dependency unavailable
- material receipt/claim mismatch
- policy exception requiring human judgment

> Manual Review is a valid business outcome, not a technical failure.

## Security and Governance

### Access
Production roles:
- Employee
- Finance Reviewer
- Finance Administrator
- Auditor

Authorization remains application-controlled.

### Privacy
- TLS in transit
- encryption at rest
- least privilege
- managed secrets
- masked logs
- defined retention/deletion
- minimum necessary LLM context

### Prompt Injection
Claim and receipt text are untrusted. The LLM cannot change:
- final decision
- approved/rejected amounts
- policy limits
- tool permissions
- payment status

## Reliability

| Failure | Behaviour |
|---|---|
| LLM unavailable | deterministic explanation |
| malformed LLM output | retry once, then fallback |
| policy retrieval unavailable | Manual Review |
| receipt service unavailable | Manual Review |
| duplicate service unavailable | Manual Review |
| Finance integration unavailable | retry / queue |
| unexpected workflow error | audit + safe routing |

## Observability

**Operational:** latency, errors, dependency availability.

**GenAI:** model latency, token usage, failure/fallback rate, retrieval quality.

**Business:** outcome mix, manual-review rate, duplicate rate, average approved amount.

Audit evidence should retain:
- trace ID
- policy ID/version/section
- validation results
- applied rules
- amounts
- decision
- explanation source
- human override

## Prototype Limitations

- one expense item per request
- domestic travel only
- four categories
- local Markdown policy
- lexical policy retrieval
- mocked receipt extraction
- local duplicate/approval data
- no ERP/HR integration
- no production IAM or immutable audit store

## Production Next Steps

1. Multi-line claims and multiple receipts.
2. Real OCR/document intelligence.
3. Enterprise hybrid/vector policy retrieval.
4. Policy version/effective-date filters.
5. ERP/HR/Finance APIs.
6. Enterprise IAM/RBAC and managed secrets.
7. Immutable audit storage and OpenTelemetry.
8. Evaluation/regression suite.
9. Async queue/worker processing if throughput/latency requires it.
