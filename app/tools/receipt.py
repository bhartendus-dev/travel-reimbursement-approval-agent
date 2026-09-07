def validate_receipt(claim) -> dict:
    """
    Prototype implementation.

    We do not perform real OCR in the 1-day MVP.
    If a receipt reference is present, we return mock extracted metadata.
    """
    expense = claim.expense
    receipt = claim.receipt

    if not receipt.available:
        return {
            "status": "MISSING",
            "receipt_found": False,
            "extraction_confidence": None,
            "extracted_amount": None,
            "file_reference": receipt.file_reference,
        }

    return {
        "status": "VALID",
        "receipt_found": True,
        "extraction_confidence": 0.98,
        "extracted_amount": expense.claimed_amount,
        "file_reference": receipt.file_reference,
    }


def is_receipt_required(policy_context: dict, claimed_amount: float) -> bool:
    rule = policy_context.get("receipt_rule", "OPTIONAL")

    if rule == "MANDATORY":
        return True

    if rule.startswith("MANDATORY_ABOVE:"):
        threshold = float(rule.split(":", 1)[1])
        return claimed_amount > threshold

    return False
