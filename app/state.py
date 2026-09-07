from typing import Any, Optional
from typing_extensions import TypedDict

from app.models import ClaimRequest


class ClaimState(TypedDict, total=False):
    claim: ClaimRequest

    policy_context: dict[str, Any]
    receipt_result: dict[str, Any]
    duplicate_result: dict[str, Any]
    approval_result: dict[str, Any]
    eligibility_result: dict[str, Any]

    decision: str
    reason_code: Optional[str]
    explanation: str
    explanation_source: str
    manual_review: bool

    trace_id: str
    audit_events: list[dict[str, Any]]
    errors: list[str]
