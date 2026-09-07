# Demo Script

Recommended duration: 5-7 minutes.

## 1. Architecture (60-90 sec)
Explain the core principle:

> GenAI interprets and explains; deterministic services validate and calculate; risky cases go to human review.

Show the component diagram and explain why the solution uses one bounded workflow rather than multiple autonomous agents.

## 2. Swagger API (30 sec)
Run:

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## 3. APPROVE Case (45 sec)
Submit `CLM-1001`.

Highlight:
- TAXI-01 retrieved
- receipt valid
- INR 800 approved
- `explanation_source = LLM_GROUNDED`

## 4. PARTIAL APPROVAL Case (60 sec)
Submit `CLM-1002`.

Highlight:
- hotel claim INR 6,200
- policy maximum INR 5,000
- deterministic engine calculates approved INR 5,000 and rejected INR 1,200
- LLM only explains the result

## 5. MANUAL REVIEW Case (45 sec)
Submit `CLM-1004`.

Highlight:
- amount is within flight limit
- mandatory receipt is missing
- no automatic approval
- safe routing to Finance

## 6. Trace Endpoint (60 sec)
Call:

```text
POST /api/v1/claims/evaluate/trace
```

Show:
- policy retrieval
- receipt validation
- duplicate check
- approval matrix
- eligibility calculation
- decision
- explanation source

## 7. Production Architecture (60 sec)
Show both deployment diagrams and briefly cover identity, secrets, policy retrieval, observability, and ERP integration.

## Closing
The system is intentionally not a chatbot or autonomous payment bot. It is a controlled decision-assistance service integrated into the Finance workflow.
