import json
from pathlib import Path

from app.graph import evaluate_claim_workflow
from app.models import ClaimRequest


def load_claims():
    raw = json.loads(
        Path("data/claims/sample_claims.json").read_text(encoding="utf-8")
    )
    return [ClaimRequest.model_validate(item) for item in raw]


def test_expected_decisions():
    claims = load_claims()
    expected = {
        "CLM-1001": ("APPROVE", 800.0),
        "CLM-1002": ("PARTIALLY_APPROVE", 5000.0),
        "CLM-1003": ("REJECT", 0.0),
        "CLM-1004": ("MANUAL_REVIEW", 0.0),
    }

    for claim in claims:
        response, trace = evaluate_claim_workflow(claim)
        decision, approved = expected[claim.claim_id]

        assert response.decision.value == decision
        assert response.amounts.approved == approved
        assert len(trace) > 0
