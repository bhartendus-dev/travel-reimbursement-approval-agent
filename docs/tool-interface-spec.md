# Tool and Interface Specification

| Tool / Service | Type | Purpose | Main Inputs | Main Outputs | Failure Handling |
|---|---|---|---|---|---|
| Policy Retrieval | Retrieval / RAG | Retrieve applicable policy evidence | category, travel type, description, expense date | policy ID, section, text, limit, receipt rule | no reliable policy -> Manual Review |
| Receipt Validation | Deterministic / document boundary | Validate receipt evidence | receipt reference, amount, category | status, extracted fields, confidence | missing required receipt / low confidence -> Manual Review |
| Duplicate Check | Deterministic | Detect potential repeat claim | employee, category, amount, date | duplicate flag, match ID/type | suspected duplicate / service unavailable -> Manual Review |
| Approval Matrix | Deterministic | Resolve required approval level | amount, employee context, category | approval level, manual-review flag | unavailable -> Manual Review |
| Eligibility Engine | Deterministic | Calculate reimbursable and rejected amount | claimed amount, eligibility, policy limit | eligible amount, rejected amount, applied rule | missing rule data -> Manual Review |
| Decision Router | Deterministic | Produce final routing outcome | all validation/tool outputs | decision, reason code, review flag | unexpected state -> Manual Review |
| LLM Explanation | GenAI | Explain already-determined result | decision, amounts, policy evidence, receipt status | structured explanation | retry/fallback to deterministic explanation |
| Audit / Trace | Deterministic | Persist decision evidence | trace ID, events, tool results | ordered audit evidence | alert; do not silently lose decision evidence |
| Finance Adapter | Integration | Send result/review case downstream | claim, decision, evidence, trace | integration status/reference | retry/queue |

## Policy Retrieval

```python
get_policy_context(
    category: str,
    description: str | None,
    travel_type: str = "DOMESTIC",
    expense_date: date | None = None,
) -> PolicyContext
```

Example output:

```json
{
  "found": true,
  "eligible": true,
  "policy_id": "TRAVEL-2026",
  "section": "HOTEL-01",
  "max_amount": 5000,
  "receipt_rule": "MANDATORY"
}
```

Production retrieval additionally filters by policy version and effective date.

## Receipt Validation

```python
validate_receipt(claim) -> ReceiptValidationResult
```

Example output:

```json
{
  "status": "VALID",
  "receipt_found": true,
  "extraction_confidence": 0.98,
  "extracted_amount": 6200
}
```

Prototype receipt data is mocked. Production can replace this service with OCR/document intelligence.

## Duplicate Check

```python
check_duplicate_claim(claim) -> DuplicateCheckResult
```

A suspected duplicate routes to Manual Review rather than automatic rejection.

## Approval Matrix

```python
get_approval_requirement(amount: float) -> ApprovalRequirement
```

Prototype thresholds are assumptions and should be externalized in production.

## Eligibility / Rules Engine

```python
calculate_reimbursement(claim, policy_context) -> EligibilityResult
```

Example:

```json
{
  "claimed_amount": 6200,
  "eligible_amount": 5000,
  "rejected_amount": 1200,
  "rule_applied": "HOTEL_MAX_LIMIT"
}
```

Financial arithmetic remains deterministic.

## Decision Router

Deterministically maps validation results to:

- `APPROVE`
- `PARTIALLY_APPROVE`
- `REJECT`
- `MANUAL_REVIEW`

The LLM cannot override this result.

## Grounded LLM Explanation

```python
generate_grounded_explanation(...) -> tuple[str, str]
```

The LLM receives:
- final decision
- approved/rejected amounts
- policy ID/section/text
- receipt status
- limited claim description

It does not receive authority to change decision or amounts.

If the model call fails:

```text
LLM_GROUNDED -> DETERMINISTIC_FALLBACK
```

## Audit / Trace

Representative events:

```text
CLAIM_RECEIVED
CLAIM_VALIDATED
POLICY_RETRIEVED
RECEIPT_VALIDATED
DUPLICATE_CHECK_COMPLETED
APPROVAL_MATRIX_CHECKED
ELIGIBILITY_CALCULATED
DECISION_DETERMINED
EXPLANATION_GENERATED
```

A common `trace_id` correlates the full decision path.
