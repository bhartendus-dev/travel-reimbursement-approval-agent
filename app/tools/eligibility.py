def calculate_reimbursement(claim, policy_context: dict) -> dict:
    claimed = float(claim.expense.claimed_amount)

    if not policy_context.get("eligible", False):
        return {
            "claimed_amount": claimed,
            "eligible_amount": 0.0,
            "rejected_amount": claimed,
            "rule_applied": "UNSUPPORTED_CATEGORY",
        }

    max_amount = policy_context.get("max_amount")

    if max_amount is None:
        return {
            "claimed_amount": claimed,
            "eligible_amount": 0.0,
            "rejected_amount": claimed,
            "rule_applied": "POLICY_LIMIT_UNAVAILABLE",
        }

    eligible = min(claimed, float(max_amount))
    rejected = max(0.0, claimed - eligible)

    return {
        "claimed_amount": claimed,
        "eligible_amount": eligible,
        "rejected_amount": rejected,
        "rule_applied": (
            "WITHIN_POLICY_LIMIT"
            if rejected == 0
            else f"{claim.expense.category.value}_MAX_LIMIT"
        ),
    }
