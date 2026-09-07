from pathlib import Path
import json


APPROVAL_MATRIX_PATH = Path("data/approval_matrix.json")


def get_approval_requirement(amount: float) -> dict:
    matrix = json.loads(APPROVAL_MATRIX_PATH.read_text(encoding="utf-8"))

    for rule in matrix["rules"]:
        min_amount = float(rule.get("min_amount", 0))
        max_amount = rule.get("max_amount")

        if amount >= min_amount and (max_amount is None or amount <= float(max_amount)):
            return {
                "approval_level": rule["approval_level"],
                "manual_review_required": bool(rule["manual_review_required"]),
            }

    return {
        "approval_level": "FINANCE",
        "manual_review_required": True,
    }
