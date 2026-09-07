from datetime import datetime, timezone
from uuid import uuid4

from langgraph.graph import StateGraph, START, END

from app.models import (
    AmountBreakdown,
    ClaimDecisionResponse,
    Decision,
    PolicyEvidence,
    ReceiptResult,
)
from app.state import ClaimState
from app.tools.policy import get_policy_context
from app.tools.receipt import validate_receipt, is_receipt_required
from app.tools.duplicate import check_duplicate_claim
from app.tools.approval import get_approval_requirement
from app.tools.eligibility import calculate_reimbursement
from app.services.explanation import generate_grounded_explanation


def _audit(state: ClaimState, event: str, details: dict | None = None) -> list[dict]:
    events = list(state.get("audit_events", []))
    events.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details or {},
        }
    )
    return events


def initialize_node(state: ClaimState) -> dict:
    trace_id = state.get("trace_id") or f"TRC-{uuid4().hex[:10].upper()}"
    return {
        "trace_id": trace_id,
        "audit_events": _audit(state, "CLAIM_RECEIVED", {"trace_id": trace_id}),
        "errors": [],
    }


def validate_claim_node(state: ClaimState) -> dict:
    claim = state["claim"]
    errors = list(state.get("errors", []))

    if claim.expense.currency != "INR":
        errors.append("Only INR claims are supported in the prototype.")

    return {
        "errors": errors,
        "audit_events": _audit(
            state,
            "CLAIM_VALIDATED",
            {"valid": len(errors) == 0},
        ),
    }


def retrieve_policy_node(state: ClaimState) -> dict:
    claim = state["claim"]
    result = get_policy_context(
        claim.expense.category.value,
        claim.expense.description,
    )
    return {
        "policy_context": result,
        "audit_events": _audit(
            state,
            "POLICY_RETRIEVED",
            {
                "policy_id": result.get("policy_id"),
                "section": result.get("section"),
                "found": result.get("found"),
            },
        ),
    }


def validate_receipt_node(state: ClaimState) -> dict:
    claim = state["claim"]
    result = validate_receipt(claim)
    required = is_receipt_required(
        state["policy_context"],
        float(claim.expense.claimed_amount),
    )
    result["required"] = required

    return {
        "receipt_result": result,
        "audit_events": _audit(
            state,
            "RECEIPT_VALIDATED",
            {"status": result["status"], "required": required},
        ),
    }


def duplicate_check_node(state: ClaimState) -> dict:
    result = check_duplicate_claim(state["claim"])
    return {
        "duplicate_result": result,
        "audit_events": _audit(
            state,
            "DUPLICATE_CHECK_COMPLETED",
            {"duplicate": result["duplicate"]},
        ),
    }


def approval_matrix_node(state: ClaimState) -> dict:
    result = get_approval_requirement(float(state["claim"].expense.claimed_amount))
    return {
        "approval_result": result,
        "audit_events": _audit(
            state,
            "APPROVAL_MATRIX_CHECKED",
            result,
        ),
    }


def eligibility_node(state: ClaimState) -> dict:
    result = calculate_reimbursement(state["claim"], state["policy_context"])
    return {
        "eligibility_result": result,
        "audit_events": _audit(
            state,
            "ELIGIBILITY_CALCULATED",
            result,
        ),
    }


def determine_decision_node(state: ClaimState) -> dict:
    claim = state["claim"]
    policy = state["policy_context"]
    receipt = state["receipt_result"]
    duplicate = state["duplicate_result"]
    approval = state["approval_result"]
    eligibility = state["eligibility_result"]

    # Safe fallback / manual review conditions first.
    if state.get("errors"):
        decision = Decision.MANUAL_REVIEW
        reason_code = "VALIDATION_ERROR"
        explanation = "; ".join(state["errors"])
        manual_review = True

    elif not policy.get("found", False):
        decision = Decision.MANUAL_REVIEW
        reason_code = "POLICY_NOT_FOUND"
        explanation = "Applicable reimbursement policy could not be determined."
        manual_review = True

    elif receipt.get("required") and not receipt.get("receipt_found"):
        decision = Decision.MANUAL_REVIEW
        reason_code = "MISSING_REQUIRED_RECEIPT"
        explanation = (
            f"A receipt is mandatory under policy {policy['section']} "
            "but no supporting receipt was provided."
        )
        manual_review = True

    elif duplicate.get("duplicate"):
        decision = Decision.MANUAL_REVIEW
        reason_code = "POSSIBLE_DUPLICATE"
        explanation = (
            f"The claim matches existing claim "
            f"{duplicate.get('existing_claim_id')} and requires Finance review."
        )
        manual_review = True

    elif approval.get("manual_review_required"):
        decision = Decision.MANUAL_REVIEW
        reason_code = "HIGH_VALUE_CLAIM"
        explanation = (
            "The claim exceeds the prototype's automatic processing threshold "
            "and requires Finance review."
        )
        manual_review = True

    elif not policy.get("eligible", False):
        decision = Decision.REJECT
        reason_code = "UNSUPPORTED_CATEGORY"
        explanation = (
            f"Expense category {claim.expense.category.value} is not eligible "
            f"under policy {policy['section']}."
        )
        manual_review = False

    elif eligibility["rejected_amount"] > 0:
        decision = Decision.PARTIALLY_APPROVE
        reason_code = "POLICY_LIMIT_EXCEEDED"
        explanation = (
            f"INR {eligibility['eligible_amount']:.2f} is eligible under "
            f"{policy['section']}; INR {eligibility['rejected_amount']:.2f} "
            "exceeds the policy limit."
        )
        manual_review = False

    else:
        decision = Decision.APPROVE
        reason_code = "WITHIN_POLICY"
        explanation = (
            f"The claim is within the allowed limit under policy {policy['section']} "
            "and required evidence is available."
        )
        manual_review = False

    return {
        "decision": decision.value,
        "reason_code": reason_code,
        "explanation": explanation,
        "manual_review": manual_review,
        "audit_events": _audit(
            state,
            "DECISION_DETERMINED",
            {
                "decision": decision.value,
                "reason_code": reason_code,
                "manual_review": manual_review,
            },
        ),
    }



def generate_explanation_node(state: ClaimState) -> dict:
    claim = state["claim"]
    eligibility = state["eligibility_result"]

    explanation, source = generate_grounded_explanation(
        deterministic_explanation=state["explanation"],
        decision=state["decision"],
        claimed_amount=eligibility["claimed_amount"],
        approved_amount=(
            0.0 if state["decision"] == Decision.MANUAL_REVIEW.value
            else eligibility["eligible_amount"]
        ),
        rejected_amount=(
            0.0 if state["decision"] == Decision.MANUAL_REVIEW.value
            else eligibility["rejected_amount"]
        ),
        policy_context=state["policy_context"],
        receipt_result=state["receipt_result"],
        claim_description=claim.expense.description,
    )

    return {
        "explanation": explanation,
        "explanation_source": source,
        "audit_events": _audit(
            state,
            "EXPLANATION_GENERATED",
            {"source": source},
        ),
    }

def build_graph():
    builder = StateGraph(ClaimState)

    builder.add_node("initialize", initialize_node)
    builder.add_node("validate_claim", validate_claim_node)
    builder.add_node("retrieve_policy", retrieve_policy_node)
    builder.add_node("validate_receipt", validate_receipt_node)
    builder.add_node("check_duplicate", duplicate_check_node)
    builder.add_node("lookup_approval", approval_matrix_node)
    builder.add_node("calculate_eligibility", eligibility_node)
    builder.add_node("determine_decision", determine_decision_node)
    builder.add_node("generate_explanation", generate_explanation_node)

    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "validate_claim")
    builder.add_edge("validate_claim", "retrieve_policy")
    builder.add_edge("retrieve_policy", "validate_receipt")
    builder.add_edge("validate_receipt", "check_duplicate")
    builder.add_edge("check_duplicate", "lookup_approval")
    builder.add_edge("lookup_approval", "calculate_eligibility")
    builder.add_edge("calculate_eligibility", "determine_decision")
    builder.add_edge("determine_decision", "generate_explanation")
    builder.add_edge("generate_explanation", END)

    return builder.compile()


graph = build_graph()


def evaluate_claim_workflow(claim) -> tuple[ClaimDecisionResponse, list[dict]]:
    result = graph.invoke({"claim": claim})

    eligibility = result["eligibility_result"]
    policy = result["policy_context"]
    receipt = result["receipt_result"]

    final_decision = Decision(result["decision"])

    # A Manual Review outcome is not an approval. Keep approved/rejected at zero
    # until a Finance reviewer makes the final disposition.
    approved_amount = (
        0.0 if final_decision == Decision.MANUAL_REVIEW
        else eligibility["eligible_amount"]
    )
    rejected_amount = (
        0.0 if final_decision == Decision.MANUAL_REVIEW
        else eligibility["rejected_amount"]
    )

    response = ClaimDecisionResponse(
        claim_id=claim.claim_id,
        decision=final_decision,
        amounts=AmountBreakdown(
            claimed=eligibility["claimed_amount"],
            approved=approved_amount,
            rejected=rejected_amount,
            currency=claim.expense.currency,
        ),
        policy_evidence=[
            PolicyEvidence(
                policy_id=policy["policy_id"],
                section=policy["section"],
                text=policy.get("text"),
            )
        ],
        receipt=ReceiptResult(
            status=receipt["status"],
            extraction_confidence=receipt.get("extraction_confidence"),
        ),
        reason=result["explanation"],
        explanation_source=result.get("explanation_source", "DETERMINISTIC_FALLBACK"),
        manual_review=result["manual_review"],
        reason_code=result.get("reason_code"),
        trace_id=result["trace_id"],
    )

    return response, result.get("audit_events", [])
