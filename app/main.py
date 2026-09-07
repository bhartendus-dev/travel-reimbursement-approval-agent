from fastapi import FastAPI, HTTPException

from app.graph import evaluate_claim_workflow
from app.models import ClaimDecisionResponse, ClaimRequest

app = FastAPI(
    title="Travel Reimbursement Approval Agent",
    version="0.2.0",
    description=(
        "Bounded agentic workflow with deterministic financial decisioning. "
    ),
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/claims/evaluate",
    response_model=ClaimDecisionResponse,
)
def evaluate_claim(claim: ClaimRequest) -> ClaimDecisionResponse:
    try:
        response, _audit_events = evaluate_claim_workflow(claim)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/v1/claims/evaluate/trace")
def evaluate_claim_with_trace(claim: ClaimRequest) -> dict:
    """
    Demo-only endpoint exposing the workflow trace.
    In production, audit details would be protected by role-based access.
    """
    try:
        response, audit_events = evaluate_claim_workflow(claim)
        return {
            "decision": response.model_dump(mode="json"),
            "audit_trace": audit_events,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
