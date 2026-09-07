from pathlib import Path
import json


DUPLICATE_DATA_PATH = Path("data/duplicate_claims.json")


def check_duplicate_claim(claim) -> dict:
    historical = json.loads(DUPLICATE_DATA_PATH.read_text(encoding="utf-8"))

    for previous in historical:
        if (
            previous["employee_id"] == claim.employee_id
            and previous["category"] == claim.expense.category.value
            and float(previous["claimed_amount"]) == float(claim.expense.claimed_amount)
            and previous["expense_date"] == claim.expense.expense_date.isoformat()
        ):
            return {
                "duplicate": True,
                "existing_claim_id": previous["claim_id"],
                "match_type": "EXACT",
            }

    return {
        "duplicate": False,
        "existing_claim_id": None,
        "match_type": None,
    }
