# Sample Inputs, Outputs, and Workflow Trace

The prototype demonstrates all four outcomes.

## Scenario 1 - APPROVE

**Claim:** Taxi, INR 800, receipt available.  
**Policy:** TAXI-01, maximum INR 2,000, receipt required above INR 500.

```json
{
  "claim_id": "CLM-1001",
  "employee_id": "EMP-101",
  "travel_type": "DOMESTIC",
  "expense": {
    "category": "TAXI",
    "claimed_amount": 800,
    "currency": "INR",
    "expense_date": "2026-08-20",
    "description": "Airport taxi to client hotel"
  },
  "receipt": {
    "available": true,
    "file_reference": "taxi_1001.pdf"
  }
}
```

Expected result:

```json
{
  "decision": "APPROVE",
  "amounts": {
    "claimed": 800,
    "approved": 800,
    "rejected": 0,
    "currency": "INR"
  },
  "policy_section": "TAXI-01",
  "receipt_status": "VALID",
  "manual_review": false,
  "reason_code": "WITHIN_POLICY"
}
```

## Scenario 2 - PARTIALLY_APPROVE

**Claim:** Hotel, INR 6,200, receipt available.  
**Policy:** HOTEL-01, maximum INR 5,000.

Deterministic calculation:

```text
eligible = min(6200, 5000) = 5000
rejected = 6200 - 5000 = 1200
```

Expected result:

```json
{
  "decision": "PARTIALLY_APPROVE",
  "amounts": {
    "claimed": 6200,
    "approved": 5000,
    "rejected": 1200,
    "currency": "INR"
  },
  "policy_section": "HOTEL-01",
  "manual_review": false,
  "reason_code": "POLICY_LIMIT_EXCEEDED"
}
```

## Scenario 3 - REJECT

**Claim:** Personal entertainment, INR 2,000.  
**Policy:** GENERAL-01, unsupported categories are ineligible.

Expected result:

```json
{
  "decision": "REJECT",
  "amounts": {
    "claimed": 2000,
    "approved": 0,
    "rejected": 2000,
    "currency": "INR"
  },
  "policy_section": "GENERAL-01",
  "manual_review": false,
  "reason_code": "UNSUPPORTED_CATEGORY"
}
```

## Scenario 4 - MANUAL_REVIEW

**Claim:** Flight, INR 12,000, mandatory receipt missing.  
**Policy:** FLIGHT-01, maximum INR 15,000 and receipt mandatory.

Expected result:

```json
{
  "decision": "MANUAL_REVIEW",
  "amounts": {
    "claimed": 12000,
    "approved": 0,
    "rejected": 0,
    "currency": "INR"
  },
  "policy_section": "FLIGHT-01",
  "receipt_status": "MISSING",
  "manual_review": true,
  "reason_code": "MISSING_REQUIRED_RECEIPT"
}
```

No amount is automatically approved while the claim is awaiting human review.

# End-to-End Trace - CLM-1002

```mermaid
sequenceDiagram
    participant U as Employee
    participant API as FastAPI
    participant G as LangGraph
    participant P as Policy Retrieval
    participant R as Receipt Validation
    participant D as Duplicate Check
    participant A as Approval Matrix
    participant E as Eligibility Engine
    participant L as LLM Explanation

    U->>API: Submit HOTEL claim INR 6,200
    API->>G: Validated ClaimRequest
    G->>P: Retrieve HOTEL policy
    P-->>G: HOTEL-01, limit INR 5,000
    G->>R: Validate receipt
    R-->>G: VALID
    G->>D: Check historical claims
    D-->>G: Not duplicate
    G->>A: Lookup approval requirement
    A-->>G: Standard processing
    G->>E: Calculate eligibility
    E-->>G: eligible 5,000; rejected 1,200
    Note over G: Deterministic decision = PARTIALLY_APPROVE
    G->>L: Explain decision with policy evidence
    L-->>G: Grounded explanation
    G-->>API: Structured decision + trace ID
    API-->>U: JSON response
```

Representative audit events:

```text
CLAIM_RECEIVED
CLAIM_VALIDATED
POLICY_RETRIEVED: HOTEL-01
RECEIPT_VALIDATED: VALID
DUPLICATE_CHECK_COMPLETED: false
APPROVAL_MATRIX_CHECKED
ELIGIBILITY_CALCULATED: approved=5000 rejected=1200
DECISION_DETERMINED: PARTIALLY_APPROVE
EXPLANATION_GENERATED: LLM_GROUNDED
```
